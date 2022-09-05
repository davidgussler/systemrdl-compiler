from typing import Optional, Dict, Any, Type, TYPE_CHECKING
from collections import OrderedDict
import inspect

from .. import component as comp

if TYPE_CHECKING:
    from .typing import PreElabRDLType

UserStructMembers = Dict[str, 'PreElabRDLType']

class UserStruct:
    """
    All user-defined structs are based on this class.

    UserStruct types can be identified using: :meth:`is_user_struct`

    Values of struct members are accessed as read-only object attributes.

    For example, the following RDL struct literal:

    .. code-block:: systemrdl

        struct my_struct {
            longint foo;
            longint bar;
        };
        ...
        my_struct_prop = my_struct'{foo:42, bar:123};

    ... can be queried in Python as follows:

    .. code-block:: python

        prop = node.get_property('my_struct_prop')

        foo = prop.foo
        bar = getattr(prop, "bar")

    If necessary, a list of a UserStruct's member names can be accessed by:

    .. code-block:: python

        member_names = prop._members.keys()
    """

    _members = OrderedDict() # type: UserStructMembers
    _is_abstract = True # type: bool
    _parent_scope = None # type: Optional[comp.Component]

    def __init__(self, values: Dict[str, Any]):
        """
        Create an instance of the struct

        values is a dictionary of {member_name : value}
        """
        if self._is_abstract:
            raise TypeError("Cannot create instance of an abstract struct type")

        # Make sure values dict matches the members allowed
        if set(values.keys()) != set(self._members.keys()):
            raise ValueError("Cannot map 'values' to this struct")

        self._values = values

    @classmethod
    def define_new(cls, name: str, members: UserStructMembers, is_abstract: bool=False) -> Type['UserStruct']:
        """
        Define a new struct type derived from the current type.

        Parameters
        ----------
        name: str
            Name of the struct type
        members: {member_name : type}
            Dictionary of struct member types.
        is_abstract: bool
            If set, marks the struct as abstract.
        """
        m = OrderedDict(cls._members)

        # Make sure derivation does not have any overlapping keys with its parent
        if set(m.keys()) & set(members.keys()):
            raise ValueError("'members' contains keys that overlap with parent")

        m.update(members)

        classdict = {
            '_members' : m,
            '_is_abstract': is_abstract,
        }
        newcls = type(name, (cls,), classdict)
        return newcls

    def __getattr__(self, name: str) -> Any:
        if name == "__setstate__":
            raise AttributeError(name)
        if name in self._values:
            return self._values[name]
        else:
            raise AttributeError("'%s' object has no attribute '%s'" % (type(self).__name__, name))

    @classmethod
    def _set_parent_scope(cls, scope: comp.Component) -> None:
        cls._parent_scope = scope

    @classmethod
    def get_parent_scope(cls) -> Optional[comp.Component]:
        """
        Returns reference to parent component that contains this type definition.
        """
        return getattr(cls, "_parent_scope", None)

    @classmethod
    def get_scope_path(cls, scope_separator: str="::") -> str:
        """
        Generate a string that represents this enum's declaration namespace
        scope.

        Parameters
        ----------
        scope_separator: str
            Override the separator between namespace scopes
        """
        parent_scope = cls.get_parent_scope()
        if parent_scope is None:
            # Importer likely never set the scope
            return ""
        elif isinstance(parent_scope, comp.Root):
            # Declaration was in root scope
            return ""
        else:
            # Get parent definition's scope path
            parent_path = parent_scope.get_scope_path(scope_separator)

            # Extend it with its scope name
            if parent_path:
                return(
                    parent_path
                    + scope_separator
                    + parent_scope._scope_name
                )
            else:
                return parent_scope._scope_name

    def __repr__(self) -> str:
        return "<struct '%s' %s at 0x%x>" % (
            self.__class__.__qualname__,
            "(%s)" % ", ".join(self._members.keys()),
            id(self)
        )

def is_user_struct(t: Any) -> bool:
    """
    Test if type ``t`` is a :class:`~UserStruct`
    """
    return inspect.isclass(t) and issubclass(t, UserStruct)
