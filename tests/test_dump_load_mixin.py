"""Test the DumpLoadMixin class."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from attr import Factory, attrs

from earwax.mixins import DumpLoadMixin

AnyDict = Dict[str, Any]


class AddressTypes(Enum):
    """Various types of address."""

    home = 0
    work = 1
    other = 2


@attrs(auto_attribs=True)
class Address(DumpLoadMixin):
    """A house address."""

    address_type: AddressTypes
    line_1: str
    city: str


@attrs(auto_attribs=True)
class Naughty(DumpLoadMixin):
    """The employee was naughty."""

    notes: str
    when: datetime = Factory(datetime.utcnow)


@attrs(auto_attribs=True)
class Employment(DumpLoadMixin):
    """Employee is employed."""

    since: datetime = Factory(datetime.utcnow)
    previous_company: Optional['Company'] = None


@attrs(auto_attribs=True)
class Person(DumpLoadMixin):
    """A person."""

    name: str
    dob: datetime
    height: float
    addresses: List[Address] = Factory(list)
    emails: List[str] = Factory(list)
    state: Optional[Union[Employment, Naughty]] = None


@attrs(auto_attribs=True)
class Department(DumpLoadMixin):
    """A department in a company."""

    name: str
    secret: bool = False
    employees: List[Person] = Factory(list)


@attrs(auto_attribs=True)
class Company(DumpLoadMixin):
    """A company."""

    name: str
    departments: Dict[str, Department] = Factory(dict)


def test_dump() -> None:
    """Test the dump method."""

    @attrs(auto_attribs=True)
    class PretendPerson(DumpLoadMixin):
        name: str
        age: int
        addresses: Dict[str, str]

    @attrs(auto_attribs=True)
    class PretendCompany(DumpLoadMixin):
        name: str
        people: List[PretendPerson] = Factory(list)

    p1: PretendPerson = PretendPerson(
        name='John Smith', age=35,
        addresses={'Home': 'Homeless', 'Work': 'Here'}
    )
    p2: PretendPerson = PretendPerson(
        name='Sally Smith', age=36, addresses={'Home': "John's place"}
    )
    c: PretendCompany = PretendCompany(name='', people=[p1, p2])
    d: AnyDict = c.dump()
    assert isinstance(d, dict)
    assert d[PretendCompany.__type_key__] == PretendCompany.__name__
    d = d[PretendCompany.__value_key__]
    assert isinstance(d, dict)
    assert d['name'] == c.name
    people: List[AnyDict] = d['people']
    assert isinstance(people, list)
    assert len(people) == 2
    d1: AnyDict
    d2: AnyDict
    d1, d2 = people
    assert d1[PretendPerson.__type_key__] == PretendPerson.__name__
    d1 = d1[PretendPerson.__value_key__]
    assert isinstance(d1, dict)
    assert d1['name'] == p1.name
    assert d1['age'] == p1.age
    assert d1['addresses'] == p1.addresses
    assert d2[PretendPerson.__type_key__] == PretendPerson.__name__
    d2 = d2[PretendPerson.__value_key__]
    assert isinstance(d2, dict)
    assert d2['name'] == p2.name
    assert d2['age'] == p2.age
    assert d2['addresses'] == p2.addresses


def test_load() -> None:
    """Test the load constructor."""
    h: Address = Address(AddressTypes.home, '1 Test Passed', 'Test Heap')
    w: Address = Address(AddressTypes.work, '3600 Mount Crash', 'Fail Gardens')
    p1: Person = Person(
        'Chris Norman', datetime(1989, 6, 14), 1.8, addresses=[h, w], emails=[
            'chris.norman2@googlemail.com', 'earwax-tests@example.com'
        ], state=Naughty('Bad employee.')
    )
    p2: Person = Person(
        'John Smith', datetime(1964, 8, 12), 1.7, state=Employment()
    )
    d: Department = Department('Coders', secret=True, employees=[p1, p2])
    c: Company = Company(
        'My Test Company', departments={'cod01': d}
    )
    data: Dict[str, Any] = c.dump()
    c2: Company = Company.load(data)
    assert c2 == c


def test_excluded_attribute_names() -> None:
    """Test the __excluded_attribute_names__ attribute."""

    @attrs(auto_attribs=True)
    class Thing(DumpLoadMixin):
        """Test thing."""

        name: str = 'Whatever'
        gender: str = 'No idea'
        __excluded_attribute_names__ = ['gender']

    t: Thing = Thing(name='Chris Norman', gender='Male')
    data: Dict[str, Any] = t.dump()
    assert data[Thing.__value_key__] == {'name': t.name}
    data[Thing.__value_key__]['gender'] = 'Female'
    t = Thing.load(data)
    assert t.name == 'Chris Norman'
    assert t.gender == 'No idea'
