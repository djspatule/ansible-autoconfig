-- Add Mason bin to PATH so nvim-lspconfig can find marksman
local mason_bin = vim.fn.stdpath("data") .. "/mason/bin"
vim.env.PATH = mason_bin .. ":" .. vim.env.PATH

return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        marksman = {},
      },
    },
  },
}
