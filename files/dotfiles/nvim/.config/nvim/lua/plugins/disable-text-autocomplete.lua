return {
  {
    "saghen/blink.cmp",
    opts = function(_, opts)
      local enabled = opts.enabled

      opts.enabled = function()
        if vim.tbl_contains({ "markdown", "markdown.mdx", "text" }, vim.bo.filetype) then
          return false
        end

        if type(enabled) == "function" then
          return enabled()
        end

        return enabled ~= false
      end
    end,
  },
}
