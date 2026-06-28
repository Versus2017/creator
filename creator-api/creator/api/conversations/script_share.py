"""脚本分享：打包 index.html + 本地图片资源为 ZIP。"""
import html
import io
import os
import re
import zipfile
from datetime import datetime
from typing import List, Dict, Any, Tuple
from urllib.parse import quote

from sqlalchemy.orm import Session

from ...config import config
from ..media.models import MediaModel
from .models import Script, ScriptMedia
from .constants import ScriptMediaType, ScriptMediaStatus


def _safe_filename(name: str, max_len: int = 36) -> str:
    s = re.sub(r'[\\/:*?"<>|\s]+', '_', (name or '').strip())
    s = s.strip('_')
    return (s[:max_len] if s else 'script')


def build_content_disposition(filename: str) -> str:
    """生成支持中文文件名的 Content-Disposition（RFC 5987）。"""
    ascii_name = re.sub(r'[^\x00-\x7F]+', '', filename)
    ascii_name = re.sub(r'[^\w.\-]', '_', ascii_name).strip('_')
    if not ascii_name or not ascii_name.endswith('.zip'):
        ascii_name = 'script_share.zip'
    encoded = quote(filename, safe='')
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded}"


def _render_markdown_basic(text: str) -> str:
    """轻量 Markdown 渲染（分享 HTML 用）。"""
    lines = (text or '').split('\n')
    parts: List[str] = []
    in_code = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('```'):
            if in_code:
                parts.append('</code></pre>')
                in_code = False
            else:
                parts.append('<pre><code>')
                in_code = True
            continue
        if in_code:
            parts.append(html.escape(line))
            continue
        if line.startswith('### '):
            parts.append(f'<h3>{html.escape(line[4:])}</h3>')
        elif line.startswith('## '):
            parts.append(f'<h2>{html.escape(line[3:])}</h2>')
        elif line.startswith('# '):
            parts.append(f'<h1>{html.escape(line[2:])}</h1>')
        elif stripped == '---':
            parts.append('<hr/>')
        elif stripped:
            parts.append(f'<p>{html.escape(line)}</p>')
    if in_code:
        parts.append('</code></pre>')
    return '\n'.join(parts)


def _share_document_styles() -> str:
    return '\n'.join([
        '* { box-sizing: border-box; margin: 0; padding: 0; }',
        'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;',
        '  background: #0a0a1a; color: rgba(255,255,255,0.9); line-height: 1.6; }',
        '.export-page { max-width: 75rem; margin: 0 auto; padding: 2rem 1.5rem 3rem; }',
        '.export-header { margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(59,130,246,0.3); }',
        '.export-header h1 { font-size: 1.75rem; font-weight: 600; color: #fff; margin-bottom: 0.5rem; }',
        '.export-subtitle { font-size: 1rem; color: rgba(255,255,255,0.75); margin-bottom: 0.75rem; }',
        '.export-meta { font-size: 0.875rem; color: rgba(255,255,255,0.5); }',
        '.export-batch { margin-bottom: 2rem; padding: 1rem; background: rgba(26,26,46,0.4);',
        '  border: 1px solid rgba(99,102,241,0.15); border-radius: 12px; }',
        '.export-batch-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; flex-wrap: wrap; }',
        '.export-tag { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }',
        '.export-tag-cover { background: rgba(139,92,246,0.25); color: #c4b5fd; }',
        '.export-tag-material { background: rgba(59,130,246,0.25); color: #93c5fd; }',
        '.export-batch-time { font-size: 0.75rem; color: rgba(255,255,255,0.45); }',
        '.export-batch-progress { font-size: 0.75rem; color: #818cf8; }',
        '.export-media-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(14rem, 1fr)); gap: 1rem; }',
        '.export-media-covers { grid-template-columns: repeat(auto-fill, minmax(12rem, 1fr)); }',
        '.export-media-item { background: rgba(15,23,42,0.5); border: 1px solid rgba(99,102,241,0.12); border-radius: 8px; overflow: hidden; }',
        '.export-media-item img { width: 100%; height: auto; display: block; cursor: zoom-in; transition: opacity 0.2s ease; }',
        '.export-media-item img:hover { opacity: 0.92; }',
        '.export-media-item figcaption { padding: 0.5rem 0.75rem; font-size: 0.75rem; color: rgba(255,255,255,0.7);',
        '  border-top: 1px solid rgba(99,102,241,0.1); line-height: 1.35; }',
        '.image-lightbox { display: none; position: fixed; inset: 0; z-index: 9999; background: rgba(0,0,0,0.88);',
        '  align-items: center; justify-content: center; padding: 1.5rem; cursor: zoom-out; }',
        '.image-lightbox.is-open { display: flex; }',
        '.image-lightbox-inner { position: relative; max-width: min(96vw, 72rem); max-height: 92vh; cursor: default; }',
        '.image-lightbox-inner img { display: block; max-width: 100%; max-height: 88vh; width: auto; height: auto;',
        '  border-radius: 8px; box-shadow: 0 20px 60px rgba(0,0,0,0.45); object-fit: contain; }',
        '.image-lightbox-caption { margin-top: 0.75rem; text-align: center; font-size: 0.875rem; color: rgba(255,255,255,0.85); }',
        '.image-lightbox-close { position: absolute; top: -0.75rem; right: -0.75rem; width: 2.25rem; height: 2.25rem;',
        '  border: none; border-radius: 50%; background: rgba(255,255,255,0.15); color: #fff; font-size: 1.25rem;',
        '  line-height: 1; cursor: pointer; backdrop-filter: blur(4px); }',
        '.image-lightbox-close:hover { background: rgba(255,255,255,0.28); }',
        '.export-media-empty { padding: 1rem; color: rgba(255,255,255,0.55); font-size: 0.875rem; }',
        '.export-section-title { font-size: 1.125rem; font-weight: 600; margin-bottom: 1rem; }',
        '.export-content { background: rgba(26,26,46,0.6); border: 1px solid rgba(59,130,246,0.2); border-radius: 8px; padding: 1.25rem 1.5rem; }',
        '.markdown-content h1,.markdown-content h2,.markdown-content h3 { font-weight: 600; margin: 1rem 0 0.5rem; }',
        '.markdown-content p { margin-bottom: 0.75rem; line-height: 1.7; }',
        '.markdown-content pre { background: rgba(10,10,26,0.6); border-radius: 8px; padding: 0.875rem; overflow-x: auto; margin: 0.75rem 0; }',
        '.markdown-content hr { border: none; border-top: 1px solid rgba(59,130,246,0.3); margin: 1rem 0; }',
    ])


def _share_lightbox_markup() -> str:
    return (
        '<div id="image-lightbox" class="image-lightbox" aria-hidden="true">'
        '<div class="image-lightbox-inner" id="image-lightbox-inner">'
        '<button type="button" class="image-lightbox-close" id="image-lightbox-close" aria-label="关闭">×</button>'
        '<img id="image-lightbox-img" src="" alt="" />'
        '<div class="image-lightbox-caption" id="image-lightbox-caption"></div>'
        '</div></div>'
    )


def _share_lightbox_script() -> str:
    return """<script>
(function () {
  var lightbox = document.getElementById('image-lightbox');
  var inner = document.getElementById('image-lightbox-inner');
  var imgEl = document.getElementById('image-lightbox-img');
  var captionEl = document.getElementById('image-lightbox-caption');
  var closeBtn = document.getElementById('image-lightbox-close');
  if (!lightbox || !imgEl) return;

  function openLightbox(src, alt, caption) {
    imgEl.src = src;
    imgEl.alt = alt || '';
    captionEl.textContent = caption || alt || '';
    lightbox.classList.add('is-open');
    lightbox.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function closeLightbox() {
    lightbox.classList.remove('is-open');
    lightbox.setAttribute('aria-hidden', 'true');
    imgEl.removeAttribute('src');
    document.body.style.overflow = '';
  }

  document.querySelectorAll('.export-media-item img').forEach(function (thumb) {
    thumb.addEventListener('click', function (e) {
      e.stopPropagation();
      var figure = thumb.closest('.export-media-item');
      var captionNode = figure ? figure.querySelector('figcaption') : null;
      openLightbox(thumb.src, thumb.alt, captionNode ? captionNode.textContent : thumb.alt);
    });
  });

  closeBtn.addEventListener('click', function (e) {
    e.stopPropagation();
    closeLightbox();
  });

  lightbox.addEventListener('click', function () {
    closeLightbox();
  });

  inner.addEventListener('click', function (e) {
    e.stopPropagation();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && lightbox.classList.contains('is-open')) {
      closeLightbox();
    }
  });
})();
</script>"""


def collect_script_media_batches(db: Session, script_id: int, user_id: int) -> List[Dict[str, Any]]:
    """与前端生成记录一致：按 created_at 倒序，每条 ScriptMedia 为一个批次。"""
    records = db.query(ScriptMedia).filter(
        ScriptMedia.script_id == script_id,
        ScriptMedia.user_id == user_id,
    ).order_by(ScriptMedia.created_at.desc()).all()

    batches: List[Dict[str, Any]] = []
    for rec in records:
        if rec.status != ScriptMediaStatus.COMPLETED.value:
            continue
        media_type = ScriptMediaType.init(rec.media_type)
        items: List[Dict[str, Any]] = []

        if media_type == ScriptMediaType.COVER:
            cover_items = rec.generated_items or []
            if cover_items:
                for seg in cover_items:
                    if not isinstance(seg, dict):
                        continue
                    if seg.get('status') != 'completed' or not seg.get('media_id'):
                        continue
                    items.append({
                        'media_id': seg['media_id'],
                        'label': (seg.get('segment_title') or '').strip() or '封面',
                        'segment_index': int(seg.get('segment_index') or 0),
                    })
            elif rec.media_id:
                items.append({
                    'media_id': rec.media_id,
                    'label': '封面',
                    'segment_index': 1,
                })
        elif media_type == ScriptMediaType.MATERIAL:
            for seg in (rec.generated_items or []):
                if not isinstance(seg, dict):
                    continue
                if seg.get('status') != 'completed' or not seg.get('media_id'):
                    continue
                items.append({
                    'media_id': seg['media_id'],
                    'label': (seg.get('segment_title') or '').strip() or f"段落 {seg.get('segment_index', '')}",
                    'segment_index': int(seg.get('segment_index') or 0),
                })

        if not items:
            continue

        completed = len(items)
        total = rec.total_segment_count or completed
        batches.append({
            'id': rec.id,
            'type_name': media_type.name,
            'type_label': media_type.label,
            'created_at': rec.created_at.strftime('%Y-%m-%d %H:%M:%S') if rec.created_at else '',
            'completed_count': completed,
            'total_count': total,
            'items': items,
            'packed_images': [],
        })
    return batches


def _build_share_html(script: Script, batches: List[Dict[str, Any]], exported_at: str) -> str:
    title = html.escape(script.title or '未命名脚本')
    subtitle = html.escape(script.subtitle or '')
    status_label = ''
    try:
        from .constants import ScriptStatus
        status_label = ScriptStatus.init(script.status).label
    except Exception:
        pass

    meta_parts = [f'导出时间：{html.escape(exported_at)}']
    if script.created_at:
        meta_parts.append(f"创建时间：{script.created_at.strftime('%Y-%m-%d %H:%M')}")
    if status_label:
        meta_parts.append(f'状态：{html.escape(status_label)}')
    meta_parts.append(f'字数：{script.word_count or 0}')

    media_html_parts: List[str] = []
    if batches:
        for batch in batches:
            tag_cls = 'export-tag-cover' if batch['type_name'] == 'COVER' else 'export-tag-material'
            progress = ''
            if batch.get('total_count'):
                unit = '张' if batch['type_name'] == 'COVER' else '段'
                progress = (
                    f'<span class="export-batch-progress">'
                    f'{batch["completed_count"]}/{batch["total_count"]} {unit}</span>'
                )
            media_html_parts.append(
                f'<div class="export-batch">'
                f'<div class="export-batch-header">'
                f'<span class="export-tag {tag_cls}">{html.escape(batch["type_label"])}</span>'
                f'{progress}'
                f'<span class="export-batch-time">{html.escape(batch["created_at"])}</span>'
                f'</div>'
                f'<div class="export-media-grid {"export-media-covers" if batch["type_name"] == "COVER" else ""}">'
            )
            for img in batch.get('packed_images') or []:
                media_html_parts.append(
                    f'<figure class="export-media-item">'
                    f'<img src="{html.escape(img["zip_path"])}" alt="{html.escape(img["label"])}" />'
                    f'<figcaption>{html.escape(img["label"])}</figcaption>'
                    f'</figure>'
                )
            media_html_parts.append('</div></div>')
    else:
        media_html_parts.append(
            '<div class="export-media-empty">暂无 AI 生成的封面或素材。</div>'
        )

    content_html = _render_markdown_basic(script.content or '')

    body = (
        f'<div class="export-page">'
        f'<header class="export-header"><h1>{title}</h1>'
        + (f'<p class="export-subtitle">{subtitle}</p>' if subtitle else '')
        + f'<p class="export-meta">{" · ".join(meta_parts)}</p></header>'
        f'<section><h2 class="export-section-title">生成素材</h2>{"".join(media_html_parts)}</section>'
        f'<section style="margin-top:2rem"><h2 class="export-section-title">脚本正文</h2>'
        f'<div class="export-content markdown-content">{content_html}</div></section>'
        f'</div>'
    )

    return (
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8" />'
        f'<meta name="viewport" content="width=device-width, initial-scale=1.0" />'
        f'<title>{title} - 脚本分享</title>'
        f'<style>{_share_document_styles()}</style></head>'
        f'<body>{body}{_share_lightbox_markup()}{_share_lightbox_script()}</body></html>'
    )


def build_script_share_zip(db: Session, script: Script, user_id: int) -> Tuple[bytes, str]:
    """构建分享 ZIP（index.html + images/），图片从磁盘复制。"""
    batches = collect_script_media_batches(db, script.id, user_id)
    media_ids: List[int] = []
    for batch in batches:
        for item in batch['items']:
            media_ids.append(item['media_id'])

    media_map: Dict[int, MediaModel] = {}
    if media_ids:
        for m in db.query(MediaModel).filter(MediaModel.id.in_(list(set(media_ids)))).all():
            media_map[m.id] = m

    upload_dir = config.UPLOADS_DEFAULT_DEST
    exported_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M')

    for batch in batches:
        type_prefix = 'cover' if batch['type_name'] == 'COVER' else 'material'
        for item in batch['items']:
            media = media_map.get(item['media_id'])
            if not media or not media.filename:
                continue
            src_path = os.path.join(upload_dir, media.filename)
            if not os.path.isfile(src_path):
                continue
            ext = os.path.splitext(media.filename)[1] or '.png'
            seg_idx = item['segment_index'] or 0
            zip_rel = (
                f"images/b{batch['id']}_{type_prefix}_{seg_idx:02d}_{_safe_filename(item['label'])}{ext}"
            )
            batch['packed_images'].append({
                'zip_path': zip_rel,
                'src_path': src_path,
                'label': item['label'],
            })

    html_content = _build_share_html(script, batches, exported_at)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('index.html', html_content.encode('utf-8'))
        written: set = set()
        for batch in batches:
            for img in batch.get('packed_images') or []:
                zip_path = img['zip_path']
                if zip_path in written:
                    continue
                zf.write(img['src_path'], zip_path)
                written.add(zip_path)

    buf.seek(0)
    zip_bytes = buf.getvalue()
    filename = f"{_safe_filename(script.title or 'script', 40)}_{exported_at.replace(':', '').replace(' ', '-')}.zip"
    return zip_bytes, filename
