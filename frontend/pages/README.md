# Why is this folder empty?

This project uses Feature-Sliced Design (FSD), whose `pages` layer lives in
`src/pages/`. Next.js would treat `src/pages/` as its legacy Pages Router, but it
ignores `src/app` and `src/pages` whenever `app/` or `pages/` exist at the project
root. This empty folder (together with the root `app/` directory that holds the App
Router routes) keeps Next.js from interpreting the FSD layer as routes.

Do not add files here. Add routes to `/app` and page compositions to `src/pages/`.
See the "Frontend architecture" section of the root README.
