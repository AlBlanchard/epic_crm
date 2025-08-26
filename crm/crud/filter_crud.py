from ..crud.base_crud import AbstractBaseCRUD


class FilterCRUD(AbstractBaseCRUD):
    def __init__(self, session):
        super().__init__(session)
