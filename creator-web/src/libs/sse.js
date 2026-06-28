/**
 * Minified by jsDelivr using Terser v5.15.1.
 * Original file: /npm/sse.js@0.6.1/lib/sse.js
 *
 * Do NOT use SRI with dynamically generated files! More information: https://www.jsdelivr.com/using-sri-with-dynamic-files
 */
export var SSE = function(t, e) {
  if (!(this instanceof SSE)) return new SSE(t, e);
  this.INITIALIZING = -1, this.CONNECTING = 0, this.OPEN = 1, this.CLOSED = 2, this.url = t, e = e || {}, this.headers = e.headers || {}, this.payload = void 0 !== e.payload ? e.payload : '', this.method = e.method || (this.payload ? 'POST' : 'GET'), this.withCredentials = !!e.withCredentials, this.FIELD_SEPARATOR = ':', this.listeners = {}, this.xhr = null, this.readyState = this.INITIALIZING, this.progress = 0, this.chunk = '', this.addEventListener = function(t, e) {
    void 0 === this.listeners[t] && (this.listeners[t] = []), -1 === this.listeners[t].indexOf(e) && this.listeners[t].push(e)
  }, this.removeEventListener = function(t, e) {
    if (void 0 !== this.listeners[t]) {
      var s = [];
      this.listeners[t].forEach((function(t) {
        t !== e && s.push(t)
      })), 0 === s.length ? delete this.listeners[t] : this.listeners[t] = s
    }
  }, this.dispatchEvent = function(t) {
    if (!t) return !0;
    t.source = this;
    var e = 'on' + t.type;
    return (!this.hasOwnProperty(e) || (this[e].call(this, t), !t.defaultPrevented)) && (!this.listeners[t.type] || this.listeners[t.type].every((function(e) {
      return e(t), !t.defaultPrevented
    })))
  }, this._setReadyState = function(t) {
    var e = new CustomEvent('readystatechange');
    e.readyState = t, this.readyState = t, this.dispatchEvent(e)
  }, this._onStreamFailure = function(t) {
    var e = new CustomEvent('error');
    e.data = t.currentTarget.response, this.dispatchEvent(e), this.close()
  }, this._onStreamAbort = function(t) {
    this.dispatchEvent(new CustomEvent('abort')), this.close()
  }, this._onStreamProgress = function(t) {
    if (this.xhr) if (200 === this.xhr.status) {
      this.readyState == this.CONNECTING && (this.dispatchEvent(new CustomEvent('open')), this._setReadyState(this.OPEN));
      var e = this.xhr.responseText.substring(this.progress);
      this.progress += e.length, e.split(/(\r\n|\r|\n){2}/g).forEach(function(t) {
        0 === t.trim().length ? (this.dispatchEvent(this._parseEventChunk(this.chunk.trim())), this.chunk = '') : this.chunk += t
      }.bind(this))
    } else this._onStreamFailure(t)
  }, this._onStreamLoaded = function(t) {
    this._onStreamProgress(t), this.dispatchEvent(this._parseEventChunk(this.chunk)), this.chunk = ''
  }, this._parseEventChunk = function(t) {
    if (!t || 0 === t.length) return null;
    var e = { id: null, retry: null, data: '', event: 'message' };
    t.split(/\n|\r\n|\r/).forEach(function(t) {
      var s = (t = t.trimRight()).indexOf(this.FIELD_SEPARATOR);
      if (!(s <= 0)) {
        var i = t.substring(0, s);
        if (i in e) {
          var h = t.substring(s + 1).trimLeft();
          'data' === i ? e[i] += h : e[i] = h
        }
      }
    }.bind(this));
    var s = new CustomEvent(e.event);
    return s.data = e.data, s.id = e.id, s
  }, this._checkStreamClosed = function() {
    this.xhr && this.xhr.readyState === XMLHttpRequest.DONE && this._setReadyState(this.CLOSED)
  }, this.stream = function() {
    for (var t in this._setReadyState(this.CONNECTING), this.xhr = new XMLHttpRequest, this.xhr.addEventListener('progress', this._onStreamProgress.bind(this)), this.xhr.addEventListener('load', this._onStreamLoaded.bind(this)), this.xhr.addEventListener('readystatechange', this._checkStreamClosed.bind(this)), this.xhr.addEventListener('error', this._onStreamFailure.bind(this)), this.xhr.addEventListener('abort', this._onStreamAbort.bind(this)), this.xhr.open(this.method, this.url), this.headers) this.xhr.setRequestHeader(t, this.headers[t]);
    this.xhr.withCredentials = this.withCredentials, this.xhr.send(this.payload)
  }, this.close = function() {
    this.readyState !== this.CLOSED && (this.xhr.abort(), this.xhr = null, this._setReadyState(this.CLOSED))
  }
};
// 'undefined' != typeof exports && (exports.SSE = SSE);
//# sourceMappingURL=/sm/6f74bb6b40f9e35313db12e8e0c96c6934e634ff065834ce83b792b1ce050ba9.map