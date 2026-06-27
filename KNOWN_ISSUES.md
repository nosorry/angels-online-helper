# Known Issues and Roadmap

This file tracks what was recently fixed and what is still pending.

## Fixed

- **English client login.** The helper finds and clicks on-screen buttons by
  matching small reference pictures of those buttons. The reference pictures for
  the **Agree** and **START** buttons were captured from the Chinese client, so
  on the English client Auto Open could not recognize the **Agree** button and
  stalled before it filled in the account and password. The bundled reference
  pictures are now captured from the English client, and English is the default.
  Reported by an English-client user.

## Still pending

- **Auto-attack on the English client.** After login, the optional auto-attack
  step looks for two in-game buttons: the attack page icon and the Auto Attack
  toggle. Those two reference pictures are still from the Chinese client. On the
  English client the helper logs in and claims rewards normally, but this step
  may not find those buttons. The step is non-blocking: if it cannot find them it
  fails quietly and the rest of the flow continues. English captures of these two
  buttons, taken at the same on-screen scale the helper runs at, are needed to
  finish it.

  Files to replace once the English buttons are captured:
  - `image/attackpage1.png` (the attack page icon)
  - `image/autoattack.png` (the Auto Attack toggle)

## Adding other languages later

Reference-picture matching is language specific, because each picture is a small
image of the button exactly as it appears on screen. To support another client
language, replace the pictures in the `image/` folder with captures from that
client at the same on-screen scale, then rebuild the executable. A future version
may bundle a separate set of pictures per language and select one at runtime.
