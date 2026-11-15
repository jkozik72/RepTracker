# Dashboard plan (chat message, 2026-11-14)

Saved verbatim from a Claude Code chat with a team member, 2026-11-14.

## Message

> Here is the plan: Postion zero is left, if the video is top down then the position is still left and right. We don't have real cameras and sensors so the "camera" will be a video and the sensors will be a finite time series, both stored in folders. When a lizard is added, I want to fill out the name, species, and a setting to configure either a top or side camera. When adding a camera, it opens a drop down of the names of the video files without the MP4. There are two sensors, there is the hot side and cold side and the hot or cold is set as left or right and then the sensors are selected similar to the video but with an option for temp with setting units and an option for humidity with setting units. The configuration is saved in a JSON format. The "camera" and "sensor" data are shown in real time, the sensor readings should be a graph with a growing window to 5 days. There is an AI side too. There is one chunk of prompts per Lizard and within that chunk, there are chunks for images from the video, created by parsing 1 image per minute and storing all of them in a single PDF and one for the context from the lizard stats. I also want a setting in settings to enable dev mode, this will allow the user to set speed of time, set moment of time, pause, and resume time on the top above alerts. In dev mode, I also want a thing per lizard for me to set a time range and a button to "generate prompts for time range" this will allow me to inspect all prompts that will be sent to the AI, then I can send it and see the stats and analysis update. This feature should handle the case for a video or range being shorter than 60mins. For all prompts, create prompt formats as files so that we can inspect them manually.

## Follow-up answers in the same chat

- Which AI provider? "We don't know yet"
- How is position scaled? "Real distance, another setting in configuring: Enclosure Width"
