import factory
from creator.test_utils import BaseFactory
from .security import generate_password_hash
from .models import BoRole, BoUser

DEFAULT_PASSWORD = '123456'


class BoRoleFactory(BaseFactory):
    class Meta:
        model = BoRole

    name = factory.Sequence(lambda n: f"role {n}")


class BoUserFactory(BaseFactory):
    class Meta:
        model = BoUser
    username = factory.Faker('name')
    password = factory.LazyFunction(
        lambda: generate_password_hash(DEFAULT_PASSWORD))
    mobile = factory.Sequence(lambda n: '1%010d' % n)
    role = factory.SubFactory(BoRoleFactory)
