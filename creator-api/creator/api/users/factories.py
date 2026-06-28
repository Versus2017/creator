import factory
from creator.test_utils import BaseFactory
from .models import User


class UserFactory(BaseFactory):
    class Meta:
        model = User

    openid = factory.Sequence(lambda n: f'wx-{n}')
    mobile = factory.Faker('phone_number')
    profile = factory.Dict(dict(
        name=factory.Faker('name'),
    ))

