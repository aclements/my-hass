Custom Home Assistant laundry monitoring
========================================

This repository contains a custom component for [Home
Assistant](https://www.home-assistant.io/) for monitoring my laundry.
It would almost certainly not work out of the box for any other
laundry setup, but it could be a useful starting point.

This component provides two states: `austin_laundry.washer` and
`austin_laundry.dryer`. Each can be one of "on", "off", or "done".
"Done" indicates that the wash or dry is complete, but that the
clothes have not yet been unloaded (specifically, the door has not
been opened since the load finished).

For the dryer, unloading is detected through power usage alone, since
opening the door turns on a light. For the washer, an additional door
open/close sensor is used to detect this.

Hardware setup
--------------

Components
- Kenmore Elite QuietPak2 washer
- Kenmore Elite QuietPak9 gas dryer
- 2x [Zooz ZEN15 v2 Z-wave plugs](https://www.getzooz.com/zooz-zen15-power-switch.html)
- 1x [Sensative Strips Guard](https://sensative.com/sensors/strips-zwave/guard/)

It's important that the dryer has a regular 120V plug. Gas dryers
typically do, but electric dryers typically do not. Other approaches
I've seen for electric dryers are to use vibration sensors or heat
sensors on the duct.

Plug the washer and dryer into the Z-wave plugs and add them to your
Z-wave network. In my case, these were the first ZEN15 plugs on my
network and I plugged associated the washer first. If this isn't the
case, the entity names in `__init__.py` will need to be changed.

I configured "Power Report Frequency" to 30 (seconds) on both plugs.
In theory this is the default, but it was showing "0".

Add the Sensative Strips to your Z-wave network and attach it to the
washer door. My washer door has a flat area at the top where the door
and the control panel meet that happened to be the perfect size and
gap. Other washers may need a different door sensor. Another option
would be to use a motion sensor in the laundry area and assume that if
someone is in the laundry room, they're unloading the laundry.

Configure the "Notification Type" of the Sensative Strip to "Binary
Sensor Report" and tap the round magnet three times on the round end
of the sensor to accept the configuration. This makes it an on/off
sensor like you would expect. (The default behavior is that the
"Sensative Strips Access Control" sensor reports "23" for closed and
"22" or open. I'm sure that means something to someone.)

Setting up the custom component
-------------------------------

Clone this repository somewhere and symlink the `austin_laundry`
directory into `$HOME/.home-assistant/custom_components`, or wherever
your Home Assistant installation lives.

To enable the component, add the following to `configuration.yaml`:

```yaml
austin_laundry:
```

If you want to enable debug logs, also add the following:

```yaml
logger:
  default: info
  logs:
    custom_components.austin_laundry: debug
```

Finally, restart Home Assistant to pick up the new configuration.

Notification automation
-----------------------

I use the following automations to send notifications when the washer
or dryer finishes and to automatically dismiss them when the clothes
are unloaded:

```yaml
- alias: Washer finished
  trigger:
  - entity_id: austin_laundry.washer
    from: 'on'
    platform: state
    to: done
  action:
  - data:
      data:
        priority: high
        tag: washer-finished
      message: Washer finished
    service: notify.notify
- alias: Dryer finished
  trigger:
  - entity_id: austin_laundry.dryer
    from: 'on'
    platform: state
    to: done
  action:
  - data:
      data:
        priority: high
        tag: dryer-finished
      message: Dryer finished
    service: notify.notify
- alias: Washer unloaded
  trigger:
  - entity_id: austin_laundry.washer
    from: done
    platform: state
    to: 'off'
  action:
  - data:
      data:
        priority: high
        tag: washer-finished
      message: clear_notification
    service: notify.notify
- alias: Dryer unloaded
  trigger:
  - entity_id: austin_laundry.dryer
    from: done
    platform: state
    to: 'off'
  action:
  - data:
      data:
        priority: high
        tag: dryer-finished
      message: clear_notification
    service: notify.notify
```

These can be configured through the Home Assistant UI.

Development notes
-----------------

To write the power analysis in the first place, I ran a few loads and
let the Home Assistant history record all the power changes. I [dumped
its logs to
CSV](https://www.home-assistant.io/blog/2016/07/19/visualizing-your-iot-data/)
so I could easily analyze and experiment with them:

```sh
cp home-assistant_v2.db /tmp/ha.db
sqlite3 -csv /tmp/ha.db "SELECT last_changed, state FROM states WHERE entity_id = 'sensor.zooz_zen15_power_switch_power' AND last_changed BETWEEN '2020-03-28 22:00:00' AND '2020-03-29 00:30:30'" > washer.csv
sqlite3 -csv /tmp/ha.db "SELECT last_changed, state FROM states WHERE entity_id = 'sensor.zooz_zen15_power_switch_power_2' AND last_changed BETWEEN '2020-03-28 23:30:00' AND '2020-03-29 02:30:30'" > dryer.csv
```

There is some sample data in the root of this repository:

- washer-1.csv: A single washer load. This includes unloading it, but
  nothing changed in the power profile to show that.
- dryer-1.csv: A dryer load shortly after washer-1. This shows
  "wrinkle protect" after the load is done as well as unloading the
  clothes (which does appear in the power profile).
- washer-2.csv: Two washer loads.
- dryer-2.csv: Two dryer loads. No wrinkle protect. Door was briefly
  opened during the first load. Clothes were left in for a while.
- dryer-3.csv: One dryer load with wrinkle protect. Door was briefly
  opened in the middle of the cycle. Shows a transient low power
  during wrinkle protect.
