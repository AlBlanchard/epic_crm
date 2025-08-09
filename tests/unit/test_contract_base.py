import pytest
from crm.models.models import Contract, Client, User
from sqlalchemy.exc import IntegrityError
from decimal import Decimal


def test_create_valid_contract(db_session, sample_users, sample_clients):
    """Contrat avec des valeurs valides."""
    sales = sample_users[0]
    client = sample_clients[0]

    contract = Contract(
        client=client,
        sales_contact=sales,
        amount_total=Decimal("1000.00"),
        amount_due=Decimal("250.00"),
        is_signed=True,
    )
    db_session.add(contract)
    db_session.flush()
    assert contract.id is not None
    assert (contract.amount_due <= contract.amount_total) is True


def test_contract_negative_total():
    """Montant total négatif interdit."""
    with pytest.raises(ValueError, match="amount_total cannot be negative"):
        Contract(
            amount_total=Decimal("-50.00"),
            amount_due=Decimal("10.00"),
            client_id=1,
            sales_contact_id=1,
        )


def test_contract_negative_due():
    """Montant dû négatif interdit."""
    with pytest.raises(ValueError, match="amount_due cannot be negative"):
        Contract(
            amount_total=Decimal("100.00"),
            amount_due=Decimal("-10.00"),
            client_id=1,
            sales_contact_id=1,
        )


def test_amount_due_greater_than_total():
    """amount_due supérieur à amount_total via validateur."""
    with pytest.raises(ValueError, match="amount_due cannot exceed amount_total"):
        Contract(
            amount_total=Decimal("100.00"),
            amount_due=Decimal("150.00"),
            client_id=1,
            sales_contact_id=1,
        )


def test_invalid_amount_type():
    """Montant de type incorrect."""
    with pytest.raises(ValueError, match="must be a numeric type"):
        Contract(
            amount_total="not a number", amount_due=100, client_id=1, sales_contact_id=1
        )


def test_missing_client_or_sales_contact(db_session):
    """Vérifie que les clés étrangères sont obligatoires."""
    contract = Contract(amount_total=Decimal("500.00"), amount_due=Decimal("100.00"))

    db_session.add(contract)
    with pytest.raises(IntegrityError):
        db_session.flush()
