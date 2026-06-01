"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from openpilot.selfdrive.ui.sunnypilot.layouts.settings.vehicle.brands.base import BrandSettings
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.sunnypilot.widgets.list_view import toggle_item_sp
from opendbc.car.mazda.values import CAR, MazdaFlags


class MazdaSettings(BrandSettings):
  def __init__(self):
    super().__init__()
    self.is_gen2 = False

    self.lowspeed_long_toggle = toggle_item_sp(tr("Low-speed Longitudinal (GEN2, Controlled-test)"), "",
                                               param="MazdaGen2LowSpeedLong", callback=self._on_toggle_changed)

    self.torque_interceptor_toggle = toggle_item_sp(tr("Torque Interceptor (TI2)"), "",
                                                    param="MazdaTorqueInterceptor", callback=self._on_toggle_changed)

    self.items = [self.lowspeed_long_toggle, self.torque_interceptor_toggle]

  def _on_toggle_changed(self, _):
    self.update_settings()

  def _disabled_msg(self):
    if not self.is_gen2:
      return tr("Only available on GEN2 Mazda (e.g. Mazda 3 2019+).")
    elif not ui_state.is_offroad():
      return tr("Enable \"Always Offroad\" in the Device panel, or turn the vehicle off to toggle. Reboot after changing.")
    return ""

  def update_settings(self):
    bundle = ui_state.params.get("CarPlatformBundle")
    if bundle:
      platform = bundle.get("platform")
      config = CAR[platform].config
      self.is_gen2 = bool(config.flags & MazdaFlags.GEN2)
    elif ui_state.CP is not None:
      self.is_gen2 = bool(ui_state.CP.flags & MazdaFlags.GEN2)

    disabled_msg = self._disabled_msg()
    desc = tr("EXPERIMENTAL — CONTROLLED-TEST ONLY. Keeps openpilot longitudinal active below the stock cruise "
              "low-speed cutoff (~13-22 km/h) by following the OEM ACC authority signal, so it can keep braking "
              "toward a stop. Only test in a safe, empty, controlled area with your foot ready to brake and hands "
              "on the wheel. Requires openpilot longitudinal. Reboot after changing for it to take effect.")
    self.lowspeed_long_toggle.action_item.set_enabled(self.is_gen2 and ui_state.is_offroad())
    self.lowspeed_long_toggle.set_description(f"<b>{disabled_msg}</b><br><br>{desc}" if disabled_msg else desc)

    ti_desc = tr("Enable only if the MoreTorque TI2 hardware is physically installed. Bypasses the EPS "
                 "low-speed steering lockout so lateral control works down to standstill. Steering stays gated "
                 "until the interceptor reports ready (TI_STATE.RUN). Controlled-test only; reboot after changing.")
    self.torque_interceptor_toggle.action_item.set_enabled(self.is_gen2 and ui_state.is_offroad())
    self.torque_interceptor_toggle.set_description(f"<b>{disabled_msg}</b><br><br>{ti_desc}" if disabled_msg else ti_desc)
