import js from "@eslint/js"
import vue from "eslint-plugin-vue"
import globals from "globals"

export default [
  {
    ignores: ["node_modules/**", "dist/**", "public/**", "src/assets/**"]
  },
  js.configs.recommended,
  ...vue.configs["flat/essential"],
  {
    files: ["**/*.cjs"],
    languageOptions: {
      sourceType: "commonjs",
      globals: {
        ...globals.node
      }
    }
  },
  {
    files: ["**/*.{js,jsx,ts,tsx,vue}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...globals.node
      }
    },
    rules: {
      "no-unused-vars": "off",
      "vue/multi-word-component-names": "off",
      "vue/no-unused-vars": "off",
      "vue/html-indent": "off",
      "vue/max-attributes-per-line": "off",
      "vue/singleline-html-element-content-newline": "off",
      "vue/multiline-html-element-content-newline": "off",
      "vue/html-closing-bracket-newline": "off",
      "vue/html-self-closing": "off",
      "vue/first-attribute-linebreak": "off",
      "vue/html-closing-bracket-spacing": "off"
    }
  }
]
