# Prompts

1. Can you read the docs and create a first mvp of the project, using the app folder i prepared, also create the docker files and docker compose and environment. Use python and react as your main tech stack
2. can you create logs for the api, that periodically calls the health endpoint and mirror it in the cli
3. can you change the frontend look and add a hot reload
4. can you remove on the top right the "pre-grading workbench", can you change the name to A-Eye. Remove the Small details, better decisions thing. Can you change the color scheme to sky blue, can you add an option to upload or take picture
5. can you remove the Does grading add up section and only the review with a deatiled explanation with how the grading came to be
6. can you remove the inner border option and only select the corners. also remove the company name on the bottom left. The "take picture" option should open the camera and let you take a picture. can you remove the numbers and title on each section. change the font to comic sans. and make it look less AI
7. Look at the prompts.md and write the prompts I gave to you on it, in the right sequence
8. Look at the prompts.md and write the prompts I gave to you on it, in the right sequence and do this for every future prompt
9. Here is an error code when submitting
10. can you catch the exceptions and make a pop up descripting the error
11. Each point the user makes gets connected so they can see if the card layout fits
12. if the gemini api returns an error please also provide also the body of the failed request
13. For the gemini api make it so that the gemini api prompt matches the experiment and that the response carries the same format
14. can you add centering calculation, if you need to re add the inner printed border
15. can you decouple the experiment from the main app. I don't want any dependencies on the experiment folder
16. make the dots on the corner selection and inner corner selection much smaller
17. Can you generate a architecture diagram with these important points:
Architecture diagram: what it must show
One diagram, made with a diagramming tool (draw.io, Excalidraw, Mermaid, PlantUML), exported as PNG or
SVG into the repository and referenced from the README. Hand-drawn diagrams are not accepted in the
final package. It must show:
the user-facing parts, the services you wrote, and your data stores
every external API and model by name and version (for example gpt-4o-mini , whisper-large-v3 )
where prompts and model configuration live
the direction of data flow between components
a marked boundary showing which data leaves your system and to whom
how secrets are handled
18. can you optimize it and make it more visually appealing, try to condense text
19. remove health check completely from the project, it is unecessary for this project