# Project brief: what RepTracker is (chat message, 2026-11-14)

- **What this is:** a team member's description of the project, sent as one chat message to Claude Code on 2026-11-14, with two whiteboard photos attached.
- **Attachments, filed next to this file in the order they were attached:** `2026-11-14-whiteboard-system-design.jpg`, `2026-11-14-whiteboard-ui.jpg`.
- **Text:** verbatim and uncorrected. The message was one paragraph; it is split into numbered sentences here so that notes can cite them (s. 1, s. 2, ...).

---

1. All right, so the project is called Rep Tracker, and it will be hosted on a single computer in a local website.
2. And the purpose of the project is to create a dashboard that can track your reptiles.
3. So we want a video, and we want a movement graph to see how much movement there was throughout the day, to track its cycles.
4. And from the movement graph, we can see its health.
5. And we want to add an LLM to do research, and then also use a VLM for analyzing images.
6. The inputs are the species, and then LLM will do research with preferably a structured output, and then it will create structured information from the research.
7. Perhaps it might collect images of the species that has a certain disease, or what it looks like healthy in general, like what the lizard looks like.
8. It might compile a bunch of this information into a folder, and then at a poll rate, when we detect that the lizard is present, we can send the image to an AI, which we don't know yet if it needs to be a VLM, or we don't know what model it needs to be.
9. But when the lizard is present, we will poll it at a certain rate.
10. And perhaps the AI analyzes if the lizard is in the frame, then it will do its analysis.
11. And if it's not in frame, then it will say that it's not in frame.
12. Now, once it does its analysis, it's going to create a structured report that will give a status of the lizard.
13. So the lizard might be shedding, or it might be overweight.
14. There's a finite amount of these different statuses that the lizard might have.
15. We want to also create statistics.
16. So we want to track when was the last time that it shedded, how long did it take.
17. There's these different things that we need to make.
18. And then in the web app side, we have a dashboard that has, on the very top, it says status and alerts.
19. And then we have sections where you can add a lizard.
20. And the lizard has a name, video, stats, movement graph, displayed.
21. And when we add a lizard, we're going to fill out a form that has the lizard, name, age, species, and maybe previous data.
22. And then for our hardware, we are not using real cameras and real sensors.
23. Instead, we are taking a video of a real lizard, and we will find videos online of other lizards in their enclosures.
24. And then the sensors will also just be a finite time series.
25. And the web app will pull from the indexes of the video.
26. So it'll pull a frame, it'll pull the sensors.
27. So in the dashboard on the website, it'll look like the video is real time, the movement graphs are being created in real time, but the reality is that the video is fully done and finite.
28. And any other video will also be fully done and finite.
29. So this simplifies real-time processing.
30. Now, we need to figure out motion tracking.
31. And we want to input a video, and then the output will be a position of the lizard.
32. If we can get a position of the lizard, I don't want to do a whole like YOLO model if it's not necessary.
33. I was thinking that we can take the derivative between frames to detect motion, and then track the motion of the lizard over time, because sometimes the lizard will not be on screen.
34. For tracking position, we were thinking of Kalman filter or Bayes filter.
35. There may be times where the frames stay the same due to how the video is being produced, and that needs to be accounted for.
36. Because when the frames stay the same, the derivative is zero, and that causes some problems if you're detecting where the lizard is.
37. For the statistics of the processed video, so the processed video we will get statistics for, and that will be position, speed, and maybe lizard present.
38. Lizard present may come from the VLM or LLM that takes an image from the video and analyzes it.
39. Preferably, I just want one AI API call per polling.
40. Here's the image from the board as well.
41. It basically tells the same data that have been set in the context before.
42. Just like visualization for you, how does it work?
