import logging
import time

from ...widgets.rules import RulesEngine, RulesDispatcher
from ...widgets.label import PyDMLabel


def test_rules_dispatcher(qapp, caplog):
    """
    Test the dispatcher to ensure that it is a singleton.

    Parameters
    ----------
    qapp

    Returns
    -------

    """
    disp1 = RulesDispatcher()
    disp2 = RulesDispatcher()
    assert disp1 is disp2

    assert disp1.rules_engine.isRunning()

    payload = {"foo": "bar"}
    disp1.dispatch(payload)

    for record in caplog.records:
        assert record.levelno == logging.ERROR
    assert "Error at RulesDispatcher" in caplog.text


def test_rules_full(qtbot, caplog):
    """
    Test the rules mechanism.

    Parameters
    ----------
    qtbot : fixture
        Parent of all the widgets
    caplog : fixture
        To capture the log messages
    """
    widget = PyDMLabel()
    qtbot.addWidget(widget)
    widget.show()
    assert widget.isVisible()

    rules = [{'name': 'Rule #1', 'property': 'Visible',
                'expression': 'ch[0] < 1',
                'channels': [{'channel': 'foo://MTEST:Float', 'trigger': True}]}]

    dispatcher = RulesDispatcher()
    dispatcher.register(widget, rules)

    re = dispatcher.rules_engine
    assert widget in re.widget_map
    assert len(re.widget_map[widget]) == 1
    assert re.widget_map[widget][0]['rule'] == rules[0]

    re.callback_value(widget, 0, 0, trigger=True, value=1)
    for record in caplog.records:
        assert record.levelno == logging.ERROR
    assert "Not all channels are connected" in caplog.text

    re.callback_conn(widget, 0, 0, value=True)
    re.callback_value(widget, 0, 0, trigger=True, value=5)
    assert re.widget_map[widget][0]['calculate'] is True
    blocker = qtbot.waitSignal(re.rule_signal, timeout=1000)
    time.sleep(2)
    assert re.widget_map[widget][0]['calculate'] is False
    blocker.wait()
    assert not widget.isVisible()

    caplog.clear()

    rules[0]['expression'] = 'foo'
    dispatcher.register(widget, rules)
    assert len(re.widget_map[widget]) == 1
    re.callback_conn(widget, 0, 0, value=True)
    re.callback_value(widget, 0, 0, trigger=True, value='a')
    time.sleep(2)
    for record in caplog.records:
        assert record.levelno == logging.ERROR
    assert "Error while evaluating Rule" in caplog.text

    dispatcher.unregister(widget)
    assert widget not in re.widget_map