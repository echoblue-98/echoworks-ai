import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		proxy: {
			// Forward all /api and /health and /metrics calls to the Python backend
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true,
			},
			'/health': {
				target: 'http://localhost:8000',
				changeOrigin: true,
			},
			'/metrics': {
				target: 'http://localhost:8000',
				changeOrigin: true,
			},
		},
	},
});
