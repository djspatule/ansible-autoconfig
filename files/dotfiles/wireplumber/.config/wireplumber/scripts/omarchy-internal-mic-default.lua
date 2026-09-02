-- WirePlumber helper: keep the laptop's internal microphone available whenever
-- no headset microphone is plugged in.
--
-- Symptom it addresses: when a wired headset (with its own microphone) is
-- unplugged, the internal mic stays muted because state-routes.lua reapplied
-- the last persisted (muted) state from ~/.local/state/wireplumber/, and the
-- default-source selection policy never overrides that mute. As a result, no
-- application finds a usable input source until something explicitly un-mutes
-- the internal mic.
--
-- This hook runs after the upstream route-selection chain and clears the
-- mute on the internal mic route (HiFi__Mic1__source) only when no headset
-- mic route (HiFi__Mic2__source) is currently available.

cutils = require ("common-utils")
devinfo = require ("device-info-cache")
log = Log.open_topic ("s-internal-mic")

local INTERNAL_MIC_NAME = "alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__Mic1__source"
local HEADSET_MIC_NAME = "alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__Mic2__source"

local function setRouteMute (device, route_index, device_id, mute)
  local param = Pod.Object {
    "Spa:Pod:Object:Param:Route", "Route",
    index = route_index,
    device = device_id,
    props = Pod.Object {
      "Spa:Pod:Object:Param:Props", "Route",
      mute = mute,
    },
    save = false,
  }
  device:set_param ("Route", param)
end

local function findRouteByName (device, target_name)
  for p in device:iterate_params ("Route") do
    local route = cutils.parseParam (p, "Route")
    if route and route.name == target_name then
      return route
    end
  end
  return nil
end

SimpleEventHook {
  name = "omarchy/internal-mic-ensure-unmuted",
  after = "device/apply-routes",
  interests = {
    EventInterest {
      Constraint { "event.type", "=", "select-routes" },
    },
  },
  execute = function (event)
    local device = event:get_subject ()
    local dev_info = devinfo:get_device_info (device)
    if not dev_info then
      return
    end

    local device_om = event:get_source ():call ("get-object-manager", "device")
    local headset_mic_available = false

    for d in device_om:iterate () do
      local routes = d.properties and d.properties["device.routes"]
      if d.properties ["device.api"] == "alsa" and routes then
        for p in d:iterate_params ("Route") do
          local route = cutils.parseParam (p, "Route")
          if route and route.name == HEADSET_MIC_NAME and route.available ~= "no" then
            headset_mic_available = true
          end
        end
      end
    end

    if headset_mic_available then
      return
    end

    for p in device:iterate_params ("Route") do
      local route = cutils.parseParam (p, "Route")
      if route and route.name == INTERNAL_MIC_NAME and route.direction == "Input" then
        if route.mute then
          log:info ("unmuting internal mic route (headset mic unavailable)")
          setRouteMute (device, route.index, route.device, false)
        end
        return
      end
    end
  end,
}
