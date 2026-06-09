return {
  {
    "mason-org/mason.nvim",
    opts = function(_, opts)
      opts.ensure_installed = opts.ensure_installed or {}
      vim.list_extend(opts.ensure_installed, { "prettier" })
    end,
  },
  {
    "stevearc/conform.nvim",
    optional = true,
    opts = function(_, opts)
      opts.formatters = opts.formatters or {}
      opts.formatters.prettier = vim.tbl_deep_extend("force", opts.formatters.prettier or {}, {
        prepend_args = function(_, ctx)
          local ft = vim.bo[ctx.buf].filetype
          if ft == "markdown" or ft == "markdown.mdx" then
            return { "--prose-wrap", "always" }
          end
          return {}
        end,
      })
    end,
  },
}
