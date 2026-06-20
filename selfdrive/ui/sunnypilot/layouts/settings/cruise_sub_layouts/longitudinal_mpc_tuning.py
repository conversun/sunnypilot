"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from collections.abc import Callable

from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.sunnypilot.widgets.list_view import option_item_sp, simple_button_item_sp
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.network import NavButton
from openpilot.system.ui.widgets.scroller_tici import Scroller


class LongitudinalMpcTuningLayout(Widget):
  def __init__(self, back_btn_callback: Callable):
    super().__init__()
    self._back_button = NavButton(tr("Back"))
    self._back_button.set_click_callback(back_btn_callback)

    items = self._initialize_items()
    self._scroller = Scroller(items, line_separator=False, spacing=0)

  def _initialize_items(self):
    self._comfort_brake = option_item_sp(
      title=lambda: tr("Comfort Brake"),
      param="LongitudinalMpcTuningComfortBrake",
      min_value=150,
      max_value=450,
      value_change_step=5,
      use_float_scaling=True,
      label_callback=lambda v: f"{v / 100.0:.2f}",
    )

    self._stop_distance = option_item_sp(
      title=lambda: tr("Stop Distance"),
      param="LongitudinalMpcTuningStopDistance",
      min_value=200,
      max_value=1200,
      value_change_step=50,
      use_float_scaling=True,
      label_callback=lambda v: f"{v / 100.0:.1f}",
    )

    self._t_follow_relaxed = option_item_sp(
      title=lambda: tr("Follow Time - Relaxed"),
      param="LongitudinalMpcTuningTFollowRelaxed",
      min_value=100,
      max_value=250,
      value_change_step=5,
      use_float_scaling=True,
      label_callback=lambda v: f"{v / 100.0:.2f}",
    )

    self._t_follow_standard = option_item_sp(
      title=lambda: tr("Follow Time - Standard"),
      param="LongitudinalMpcTuningTFollowStandard",
      min_value=100,
      max_value=220,
      value_change_step=5,
      use_float_scaling=True,
      label_callback=lambda v: f"{v / 100.0:.2f}",
    )

    self._t_follow_aggressive = option_item_sp(
      title=lambda: tr("Follow Time - Aggressive"),
      param="LongitudinalMpcTuningTFollowAggressive",
      min_value=80,
      max_value=180,
      value_change_step=5,
      use_float_scaling=True,
      label_callback=lambda v: f"{v / 100.0:.2f}",
    )

    self._x_ego_obstacle_cost = option_item_sp(
      title=lambda: tr("Distance Cost"),
      param="LongitudinalMpcTuningXEgoObstacleCost",
      min_value=50,
      max_value=600,
      value_change_step=25,
      use_float_scaling=True,
      label_callback=lambda v: f"{v / 100.0:.2f}",
    )

    self._j_ego_cost = option_item_sp(
      title=lambda: tr("Jerk Cost"),
      param="LongitudinalMpcTuningJEgoCost",
      min_value=100,
      max_value=1500,
      value_change_step=50,
      use_float_scaling=True,
      label_callback=lambda v: f"{v / 100.0:.2f}",
    )

    self._a_change_cost = option_item_sp(
      title=lambda: tr("Acceleration Change Cost"),
      param="LongitudinalMpcTuningAChangeCost",
      min_value=5000,
      max_value=60000,
      value_change_step=500,
      use_float_scaling=True,
      label_callback=lambda v: f"{v / 100.0:.0f}",
    )

    self._danger_zone_cost = option_item_sp(
      title=lambda: tr("Danger Zone Cost"),
      param="LongitudinalMpcTuningDangerZoneCost",
      min_value=0,
      max_value=50000,
      value_change_step=500,
      use_float_scaling=True,
      label_callback=lambda v: f"{v / 100.0:.0f}",
    )

    self._lead_danger_factor = option_item_sp(
      title=lambda: tr("Lead Danger Factor"),
      param="LongitudinalMpcTuningLeadDangerFactor",
      min_value=25,
      max_value=150,
      value_change_step=5,
      use_float_scaling=True,
      label_callback=lambda v: f"{v / 100.0:.2f}",
    )

    self._reset_button = simple_button_item_sp(
      button_text=lambda: tr("Reset to Defaults"),
      button_width=720,
      callback=self._reset_defaults,
    )

    items = [
      self._comfort_brake,
      self._stop_distance,
      self._t_follow_relaxed,
      self._t_follow_standard,
      self._t_follow_aggressive,
      self._x_ego_obstacle_cost,
      self._j_ego_cost,
      self._a_change_cost,
      self._danger_zone_cost,
      self._lead_danger_factor,
      self._reset_button,
    ]
    return items

  def _reset_defaults(self):
    defaults = {
      "LongitudinalMpcTuningComfortBrake": 2.5,
      "LongitudinalMpcTuningStopDistance": 6.0,
      "LongitudinalMpcTuningTFollowRelaxed": 1.75,
      "LongitudinalMpcTuningTFollowStandard": 1.45,
      "LongitudinalMpcTuningTFollowAggressive": 1.25,
      "LongitudinalMpcTuningXEgoObstacleCost": 3.0,
      "LongitudinalMpcTuningJEgoCost": 5.0,
      "LongitudinalMpcTuningAChangeCost": 200.0,
      "LongitudinalMpcTuningDangerZoneCost": 100.0,
      "LongitudinalMpcTuningLeadDangerFactor": 0.75,
    }
    for key, value in defaults.items():
      ui_state.params.put(key, value)
    for item in self._scroller.widgets:
      item.show_event()

  def _render(self, rect):
    self._scroller.render(rect)

  def show_event(self):
    self._scroller.show_event()

  def _handle_mouse_release(self, mouse_pos):
    return self._scroller._handle_mouse_release(mouse_pos)

  def _update_state(self):
    super()._update_state()
    has_long = ui_state.has_longitudinal_control
    for item in self._scroller.widgets:
      if hasattr(item, "action_item"):
        item.action_item.set_enabled(has_long)
