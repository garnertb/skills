/** @type {import("prettier").Config} */
export default {
  overrides: [
    {
      files: "**/*.md",
      options: {
        parser: "markdown",
        proseWrap: "always",
        printWidth: 80,
        tabWidth: 2,
        useTabs: false,
      },
    },
  ],
};
