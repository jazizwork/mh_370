# MH370: Could a plane's sound find it? A public-data reanalysis

Voice-over script for ElevenLabs. Target length is about 18 minutes at roughly 150 words per minute.

How to read this file:
- **NARRATION** is the text to paste into ElevenLabs, one scene per generation. The build step writes TTS-ready copies with the pronunciation fixes applied to `video/tts/Sxx.txt`.
- **ONSCREEN** lists short captions and lower-thirds for the edit.
- **VISUALS** lists figure IDs, described in `video/visuals.md`.

Pronunciation (applied automatically to the TTS copies):
- WSPR → "whisper"
- IMOS → "eye-moss"
- colsto → "col-sto"
- CSIRO → "C-S-I-R-O"
- ATSB → "A-T-S-B"
- DSTG → "D-S-T-G"
- Réunion → "ray-union"
- UTC → "U-T-C"
- MH370 → "M H three seventy"
- flight 370 → "flight three seventy"

All times in the narration are Malaysian local time (UTC+8) unless stated.

---

## S01 | Cold open
VISUALS: V00_colsto_ref, V02_doppler_concept, V01_title
ONSCREEN: "Early November 2026: a YouTuber shows plane noise can geolocate a video" | "Could the same idea find MH370?" | "I asked Claude, Anthropic's AI, to help me find out"
NARRATION:
Earlier this month, a YouTuber called colsto showed something unsettling. A faint propeller plane, droning in the background of a video, can be enough to work out where that video was filmed. As the plane passes, the pitch of its engine bends, from high to low. Match that bend against public flight-tracking data, and you can pin the camera down, sometimes to within a hundred metres.

I wondered if that idea could help us find MH370.

The answer to that is no. However, it led me down a rabbit hole of trying to see what I could do, using only data that anyone can download. That rabbit hole turned into a full reanalysis of where the plane went, and that's what this video is about.

## S02 | What happened
VISUALS: V03_flight_path
ONSCREEN: "8 March 2014 · 239 people on board" | "01:19 'Good night, Malaysian three seven zero'" | "02:22 last military radar contact"
NARRATION:
On the eighth of March 2014, Malaysia Airlines flight 370 left Kuala Lumpur for Beijing at 12:42 in the morning. There were 239 people on board.

Thirty-seven minutes later, as the flight was handed from Malaysian to Vietnamese air traffic control, the captain said: "Good night, Malaysian three seven zero." Less than two minutes after that, the transponder, the device that identifies the plane on air traffic control screens, went silent.

Malaysian military radar, which doesn't need the transponder, kept watching. It saw the aircraft turn back, cross the Malay Peninsula, pass Penang and head out over the Strait of Malacca. The last radar contact was at 2:22 in the morning, over the Andaman Sea, north-west of Sumatra.

After that, nobody saw the plane again. But something on board was still talking.

## S03 | The satellite arcs
VISUALS: V04_arcs_map, V05_bfo_chart
ONSCREEN: "Timing → distance → a ring" | "Frequency → Doppler → direction" | "08:19 · the 7th arc"
NARRATION:
At 2:25, the plane's satellite terminal logged back on to an Inmarsat satellite over the Indian Ocean. For the next six hours, it answered automatic "are you there?" messages, roughly once an hour. Those messages carried no position. But each one recorded two numbers.

The first is a timing value. It tells you how far the plane was from the satellite, which puts it somewhere on a ring on the Earth's surface. Seven messages, seven rings. The last one, at 8:19 in the morning, is the famous seventh arc.

The second number is a frequency offset. It's a Doppler measurement: the same physics as the plane-sound trick, but applied to a radio signal instead of sound. It depends on how fast the plane was moving towards or away from the satellite. That is what told investigators the plane flew south, into the southern Indian Ocean, rather than north over Asia.

So the satellite data had already done what we hoped the sound trick might do. It turned a Doppler shift into a track. Just a very blurry one.

## S04 | Where people have looked
VISUALS: V06_search_timeline, V07_searched_map
ONSCREEN: "ATSB 2014–17 · ~120,000 km²" | "Ocean Infinity 2018 · ~112,000 km²" | "Ocean Infinity 2025–26 · 7,571 km²"
NARRATION:
That blur is the whole problem. The seventh arc is thousands of kilometres long. Fuel, speed and the satellite data narrow it down, but only so far.

In 2014, ships and aircraft searched millions of square kilometres of ocean surface. A hunt for the black box pingers came up empty. Then the Australian Transport Safety Bureau led a deep-sea sonar search along the arc, from about 33 to 39 and a half degrees south, reaching roughly 25 to 50 nautical miles either side. That was around 120,000 square kilometres, nearly three years, and close to 200 million Australian dollars. It was suspended in January 2017.

In 2018, the company Ocean Infinity searched more than 112,000 square kilometres, mostly further north along the arc. Nothing.

In 2025, Malaysia signed a "no find, no fee" deal with Ocean Infinity. Over 28 days at sea, their robots covered about 7,500 square kilometres near the spot independent researchers had ranked most likely. Nothing again. In June this year, the contract was extended to mid-2027, with about 7,400 square kilometres still to go.

Altogether, about a quarter of a million square kilometres of seabed has been mapped. That's roughly the size of the United Kingdom.

## S05 | The debris
VISUALS: V08_debris_map
ONSCREEN: "29 July 2015 · flaperon found on Réunion" | "~20 pieces judged likely or certain" | "None found in Western Australia"
NARRATION:
Meanwhile, the ocean started giving pieces back. In July 2015, a wing part called a flaperon washed up on Réunion Island. Over the next two years, more pieces turned up in Mozambique, South Africa, Tanzania, Mauritius and Madagascar. In all, about twenty have been judged likely or certain to be from the plane. Nothing was found in Western Australia.

Oceanographers tried to run the currents backwards to find where the debris started. They didn't agree. Some studies landed near 35 degrees south. Others landed much further north, between 25 and 30. We'll come back to why.

## S06 | The other leads
VISUALS: V09_leads_map
ONSCREEN: "Sound candidates · Curtin 2014 · Anderson 2018 · Kadri 2024" | "WSPR amateur-radio claim · 29.1°S 99.9°E · never searched"
NARRATION:
There were also leads from other sensors.

Underwater microphones off Western Australia, some run for the nuclear test-ban treaty, recorded several sounds that morning. In 2014, researchers at Curtin University traced one of them, and later concluded it was most likely geological. In 2024, a peer-reviewed paper by Usama Kadri highlighted a different faint arrival, called it inconclusive, and proposed test explosions along the arc to check it. An independent analyst, Ed Anderson, has argued for a sound source off the coast of Java.

And since 2021, a team led by Richard Godfrey has claimed that MH370 can be tracked using WSPR, a worldwide network of amateur radio beacons, by looking for tiny disturbances where the plane crossed radio paths. Their proposed crash site, near 29 degrees south, has never been searched.

None of these leads has found the plane. Part of our work was testing each of them, using only open data.

## S07 | Can you reverse the sound trick?
VISUALS: V10_sound_footprint
ONSCREEN: "Jet at ~35,000 ft · broadband roar" | "Sound reaches the ground only near the track" | "Open ocean · night · engines out by the last ping"
NARRATION:
First, the question that started all this. Could you run the plane-sound trick in reverse, using microphones in known places to track an unknown plane?

For MH370, no. The trick works on propeller aircraft, which hum at a steady low pitch you can follow. MH370 was a Boeing 777 with jet engines, cruising at around 35,000 feet, where jet noise is mostly a broad roar. And because the air near the ground is much warmer than the air up there, sound coming down at a shallow angle bends back upwards, so it only reaches the ground in a narrow strip either side of the flight path. After 2:22 in the morning, the plane was over open ocean at night, with no microphones anywhere beneath it. And by the final satellite message, investigators believe both engines had already run out of fuel. There was no engine tone left to hear.

The satellite frequency data is already the reverse-Doppler measurement, and it already exists. So instead of hunting for a new sensor, we went back to the evidence we have and rebuilt it from scratch.

## S08 | What we did differently
VISUALS: V11_approach_diagram
ONSCREEN: "Research, code and analysis built with Claude" | "Public data only" | "Validated against published numbers" | "Satellite + drift + everything already searched" | "Including: what if our model is wrong?"
NARRATION:
Here's what's different about this analysis.

One: we used only data that anyone can download for free. No government data requests and no special access. That covers the Inmarsat log released in 2014, Geoscience Australia's maps of exactly where the sonar searches went, Malaysia's official search updates, NOAA's ocean drifter records, ERA5, which is a global reconstruction of the weather on any past day, underwater recordings from IMOS, Australia's ocean-monitoring network, and open seismometer networks.

Two: we rebuilt every piece independently, and checked it against published numbers before trusting it. Our satellite model reproduces the Inmarsat team's own published worked example to within about one hertz, which is as precise as the measurements themselves.

Three: instead of producing one more crash point, we combined independent layers. The satellite data. The debris drift. And, crucially, a map of every patch of seabed that has already been searched, and how thoroughly. We tested the sound recordings too, but nothing in them was solid enough to add. Then we asked a different question. Not "where is the most likely spot?", but "given where people have already looked, where is the probability that's left?"

And four: every assumption that matters gets a stress test, including the possibility that our own model is wrong.

## S09 | Finding one: the satellite data points to the high thirties, but can't settle it alone
VISUALS: V12_satcom_profile, V13_satcom_paths
ONSCREEN: "Final turn south: ~02:32–02:40" | "Median end point: 38.2°S · 90% range 36.5–39.5°S" | "34.2°S route fits only with a descent at 02:40" | "Level at 02:40: off by 39 Hz"
NARRATION:
Finding one. The satellite data points to the high thirties south, but on its own it can't settle the argument.

We modelled the flight after the turn south the way a pilot could have set up the autopilot. Either one fixed setting, like a constant compass course, or a route through one of the published navigation waypoints in the area followed by a new course. We used the real winds from that night and let the data score every option.

The best fits make the final turn south between about 2:32 and 2:40, then cruise at around 80 per cent of the speed of sound, a normal cruising speed. Most of them end up near 38 degrees south, with a 90 per cent range from about 36 and a half to 39 and a half. That's very close to the official analysis by Australia's defence scientists.

Now the important part. The most popular independent hotspot, near 34.2 degrees south, is where the 2025 search went. Its route only fits if the plane was descending during a phone call attempt at 2:40. If the plane was flying level at that moment, the frequency recorded during the call is off by 39 hertz. That's a big miss, because these measurements are good to within a few hertz. If it was descending, the route fits as well as ours. Nothing in the data tells us which. So the satellite data alone can't choose between 38 and 34 degrees south. That comes down to assumptions nobody can check.

## S10 | Finding two: the drift studies disagreed for a reason
VISUALS: V14_drift_profiles, V15_drift_speed
ONSCREEN: "Drifter-based models run ~20% slow → origin shifts north" | "Default drift peak: 33.4°S" | "Flaperon with measured leeway: ~38°S"
NARRATION:
Finding two. The debris doesn't really disagree with the satellite data. The models did.

We built a drift model from more than three million five-day movements of real ocean drifters that had lost their underwater sails, which makes them ride the surface the way debris does. When we tested it against drifters it had never seen, we found a problem. Models built this way move debris about 20 per cent too slowly. That bias pushes the predicted starting point north, and it explains why several published studies ended up between 25 and 30 degrees south.

Correct for the bias, and the debris points to roughly 31 to 35 degrees south, peaking near 33.4.

Then there's the flaperon. In sea trials, CSIRO scientists found that a real flaperon drifts faster than other debris, and about 20 degrees to the left of the wind. Treat it as generic debris, and it points to about 30 degrees south. Use its measured behaviour instead, and it points to about 38. That's right where the satellite data is.

So the north–south split in the drift studies comes mostly from two modelling choices, not from the debris itself.

## S11 | Finding three: the sound candidates don't hold up
VISUALS: V16_acoustic_timing, V17_spectrogram
ONSCREEN: "4.7 GB of open IMOS recordings + 8 control nights" | "Kadri 2024: 11–17 min too late" | "Java event: natural earthquake, ~M4.1" | "Nothing above chance along the arc"
NARRATION:
Finding three. None of the sound candidates holds up on open data.

We downloaded 4.7 gigabytes of public underwater recordings from Australia's IMOS network, covering that night and eight quiet control nights. We rewrote the file reader and checked it against the operator's own processed data. It matches to within three hundredths of a decibel, and it clearly picks up earthquakes thousands of kilometres away.

The 2024 candidate arrives 11 to 17 minutes too late for an impact on the seventh arc. On the recorder we could check, the 2014 Curtin event looks like a whale call, a knock on the mooring, and then the sound of an earthquake. The Java event is real, but it's a natural earthquake of about magnitude 4.1, releasing roughly 20 times the energy of a 777 hitting the sea.

One faint arrival at Cape Leeuwin, flagged by Los Alamos in 2014, does have timing that fits a crash near 41 degrees south. But nothing on any open sensor backs it up, so with public data it can't be tested either way.

Across the whole arc, the recordings show nothing above what chance alone would produce.

## S12 | Finding four: the WSPR method has a physics problem
VISUALS: V18_wspr_physics, V19_wspr_coverage
ONSCREEN: "Needed: ~1 dB change" | "Physics allows: ~0.03 dB" | "Natural jitter: 3.5–5 dB" | "No direct WSPR link over the southern arc after 07:06"
NARRATION:
Finding four. The WSPR method has a physics problem.

WSPR reports signal strength in steps of one decibel. For a plane to show up at all, its reflected signal has to shift a reading by about one decibel. We worked out how much radio energy a 777 can actually reflect at these frequencies and distances. The largest change it can plausibly make is about three hundredths of a decibel. Meanwhile, the same radio link naturally jumps by three and a half to five decibels from one reading to the next. We measured that ourselves in the public WSPR database.

We also checked what the network could actually see that night. After 7:06 in the morning, not one WSPR signal path, from a transmitter to a receiver, crossed the southern part of the arc. The final hour of the flight wasn't covered at all.

And the statistics are thin. The team's own published test of the method scores close to what you'd get by guessing, within its margin of error.

The WSPR team disagrees with these criticisms. The fair way to settle it is a blind test. Take hundreds of modern flights with known positions, hide which is which, and see whether the method can find them. All the data for that is public, and we've written out exactly how to run it.

## S13 | The uncomfortable part
VISUALS: V20_searched_vs_unsearched, V26_model_wrong
ONSCREEN: "86% of the satellite probability is on seabed already searched" | "If the model were right: only a 6–17% chance every search misses" | "'Model is wrong somewhere': 1 in 10 → nearly 1 in 2"
NARRATION:
Now put the layers together, and you hit the uncomfortable part.

About 86 per cent of the satellite-data probability sits on seabed that has already been searched, mostly by the 2014 to 2017 search, which reported detection rates above 95 per cent. If our satellite model were right, the chance that every search would have missed the plane is only about 6 to 17 per cent, depending on how much weight you give the debris drift.

That makes the empty searches evidence that the model is wrong somewhere. So we gave the analysis a deliberately vague alternative: the plane could have ended anywhere along the arc between 20 and 42 degrees south. We started by giving that alternative only a one-in-ten chance of being the right picture, then let the failed searches and the debris drift update it. It rises to nearly one in two.

In plain terms, after a quarter of a million square kilometres of empty seabed, the honest position is roughly fifty-fifty. Either the standard picture is right and something was missed, or something about the standard picture is wrong.

## S14 | Where the probability is now
VISUALS: V21_results_map, V22_area_cards
ONSCREEN: "No single search-sized area holds more than ~1 chance in 10" | "1 · 30.46°S 98.41°E · ~8.5%" | "2 · 38.75°S 89.02°E · ~5%" | "3 · 32.36°S 96.89°E · ~4%" | "Satellite-only pick: 39.94°S 84.82°E"
NARRATION:
So where does that leave the probability? Spread out. No single search-sized area holds more than about one chance in ten. But a clear pattern shows up.

Almost all of the best remaining areas sit on the far side of the arc, the side the plane was heading towards, between about 40 and 130 kilometres beyond it. That's just outside the width the searches covered. If the plane carried on a little further than people assumed after its fuel ran out, it would be in ground nobody has looked at.

Here are the top three, each about 7,500 square kilometres, roughly what one search season can cover.

Area one is centred on thirty point four six degrees south, ninety-eight point four one east. It's a long strip 40 to 60 kilometres beyond the arc, right along the outer edge of the 2018 search. Under our default assumptions it comes out on top whenever the debris drift is included, whichever version of the satellite model we use, though small changes to the assumptions can swap the order of the top two. It holds about 8 and a half per cent of the remaining probability.

Area two is centred on thirty-eight point seven five south, eighty-nine point zero two east, 90 to 130 kilometres beyond the arc, where a piloted glide after the fuel ran out would end. About 5 per cent.

Area three is centred on thirty-two point three six south, ninety-six point eight nine east, 60 to 80 kilometres beyond the arc. About 4 per cent.

If you set the debris drift aside and trust only the satellite data, the top pick changes. It becomes the stretch of arc just past the southern end of the 2014 to 2017 search, around thirty-nine point nine four south, eighty-four point eight two east.

Two more results. Area one lies near the crash site proposed using WSPR, but not on it. That's a coincidence of geography. Our analysis doesn't use WSPR at all, and our criticisms of that method still stand. And the strip still left in Ocean Infinity's current contract lies on the near side of the arc. To end up there, the plane would have had to turn back after its final message, and in our model it gets almost no probability.

## S15 | How this explains the history
VISUALS: V23_history_explained
ONSCREEN: "2014–17: right latitudes, limited width" | "2018: further north, limited width; area 1 sits on its outer edge" | "2025–26: hotspot depends on a descent at 02:40" | "The empty searches point past the edges"
NARRATION:
This also helps explain why the past searches came up empty.

The 2014 to 2017 search went to the latitudes the satellite data favours, and our analysis agrees with that choice. But it covered a band only a few dozen nautical miles wide around the arc. If the plane carried on further after its fuel ran out, it would lie just outside.

The 2018 search went further north along the arc, again over a limited width. Our top area sits right along its outer edge.

The 2025 search went to the independent hotspot near 34 degrees south. That spot depends on the plane descending at 2:40, which may or may not have happened.

The sound candidates fail on timing or energy. And the WSPR crash point has moved by around four degrees over the years as the method changed, which is what you'd expect if the signal is mostly noise.

None of this means those teams were careless. Each search followed the best analysis of its time. What's changed is that, taken together, the empty searches have become evidence in their own right. And they point past the edges.

## S16 | What could prove us wrong
VISUALS: V24_limits
ONSCREEN: "How much to doubt the model is a judgement call" | "No public fuel model" | "2025–26 footprint reconstructed" | "Search thoroughness partly estimated" | "Flaperon drift check: currents to mid-2015 only"
NARRATION:
Some honest limits. This is an independent analysis, not an official one. How much to doubt the satellite model in the first place is a judgement call. We started at one in ten, and if you change that, the top two areas can swap places. We couldn't find a public fuel-burn model good enough to use. The 2025 to 2026 search footprint has never been published, so we reconstructed it from ship-tracking data. How thoroughly each past search covered its ground is partly our own estimate. And our check on the flaperon's drift only uses ocean currents up to mid-2015.

Any of those could move the answer. If you have better data on any of them, it should go into the model.

## S17 | Close
VISUALS: V25_close
ONSCREEN: "Code, data sources and full reports: link in description" | "239 people"
NARRATION:
We started with a clever trick for locating videos, and ended up somewhere much less glamorous. Rereading old data carefully. Testing every lead the same way. And keeping track of where people have already looked.

It doesn't find MH370. What it does is show where the remaining probability actually sits, with coordinates, and say honestly how little of it any single area holds.

Everything we used, the code, the data sources and the full reports, is linked in the description. If you can show it's wrong, please do.

Two hundred and thirty-nine people were on that plane. Their families still don't know where they are. That's the reason to keep checking.
