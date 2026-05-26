import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, loadEnv } from 'vite';

// API proxy target — defaults to local dev API, override with VITE_API_TARGET env
// (e.g. VITE_API_TARGET=http://172.16.254.150:8000 npm run dev) to point the
// laptop frontend at M7's sovereign inference API over the LAN.
export default defineConfig(({ mode }) => {
	const env = loadEnv(mode, process.cwd(), '');
	const apiTarget = env.VITE_API_TARGET || 'http://localhost:8000';

	return {
		plugins: [sveltekit()],
		server: {
			proxy: {
				'/api': { target: apiTarget, changeOrigin: true },
				'/health': { target: apiTarget, changeOrigin: true },
				'/metrics': { target: apiTarget, changeOrigin: true },
			},
		},
	};
});
