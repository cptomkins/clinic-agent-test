import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import svg from '@poppanator/sveltekit-svg';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [
    sveltekit(),
    tailwindcss(),
    svg()
  ],
  server: {
    host: true,
    allowedHosts: ['app.localtest.me'],
  },
});
