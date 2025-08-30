import pytest
from unittest.mock import MagicMock, patch
from crm.controllers.filter_controller import FilterController


@pytest.fixture
def controller():
    ctrl = FilterController(session=MagicMock())
    ctrl._setup_services()
    # Mock dépendances
    ctrl.controllers = {
        "clients": MagicMock(),
        "contracts": MagicMock(),
        "events": MagicMock(),
    }
    ctrl.view = MagicMock()
    ctrl.app_state = MagicMock()
    return ctrl


# ---------- list_filtered ----------
def test_list_filtered_success(controller):
    fake_result = [{"id": 1}]
    controller.controllers["clients"].list_all.return_value = fake_result

    result = controller.list_filtered("clients", {"company_name": "TestCo"})

    assert result == fake_result
    controller.controllers["clients"].list_all.assert_called_once_with(
        filters={"company_name": "TestCo"}
    )


def test_list_filtered_invalid_entity(controller):
    with pytest.raises(ValueError):
        controller.list_filtered("invalid", {})


def test_list_filtered_invalid_field(controller):
    with pytest.raises(ValueError):
        controller.list_filtered("clients", {"not_allowed": "x"})


def test_list_filtered_internal_error(controller):
    controller.controllers["clients"].list_all.side_effect = Exception("boom")
    with pytest.raises(ValueError) as exc:
        controller.list_filtered("clients", {"company_name": "X"})
    assert "Erreur lors de la récupération" in str(exc.value)


# ---------- show_filter_menu ----------
def test_show_filter_menu_no_entity(controller):
    controller.show_filter_menu(None)
    controller.app_state.set_error_message.assert_called_once_with(
        "Veuillez spécifier une entité à filtrer."
    )


def test_show_filter_menu_choose_filter_none(controller):
    controller.view.choose_filter.return_value = None
    controller.show_filter_menu("clients")
    controller.app_state.set_error_message.assert_called_once_with(
        "Veuillez spécifier un filtre."
    )


def test_show_filter_menu_enter_filter_criteria_none(controller):
    controller.view.choose_filter.return_value = {"field": "company_name"}
    controller.view.enter_filter_criteria.return_value = None
    controller.show_filter_menu("clients")
    controller.app_state.set_error_message.assert_called_once_with(
        "Veuillez spécifier un filtre."
    )


def test_show_filter_menu_success(controller):
    fake_filter = {"company_name": "TestCo"}
    fake_result = [{"id": 1}]
    controller.view.choose_filter.return_value = {"field": "company_name"}
    controller.view.enter_filter_criteria.return_value = fake_filter
    controller.list_filtered = MagicMock(return_value=fake_result)

    controller.show_filter_menu("clients")

    controller.view.list_filtered.assert_called_once_with("clients", fake_result)
