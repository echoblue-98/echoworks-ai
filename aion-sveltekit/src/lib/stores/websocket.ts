import {
	connectionStatus,
	stats,
	addLine,
	activeAttack,
	currentReport,
	reportLoading,
	currentDocAnalysis,
	docAnalysisLoading,
	triggerShake,
	voiceEnabled
} from './state';
import type { DocumentAnalysisResult } from './state';
import { fallbackScenarios } from '$lib/data/content';

const WS_URL = 'ws://localhost:8765';
let ws: WebSocket | null = null;
let reconnectAttempts = 0;
const MAX_RECONNECT = 3;
let isConnecting = false;

// ── Public API ─────────────────────────────────────────

export function connect() {
	if (isConnecting || (ws && ws.readyState === WebSocket.OPEN)) return;
	isConnecting = true;
	connectionStatus.set('connecting');

	try {
		if (ws) {
			ws.onclose = null;
			ws.close();
		}
		ws = new WebSocket(WS_URL);

		ws.onopen = () => {
			isConnecting = false;
			reconnectAttempts = 0;
			connectionStatus.set('connected');
			addLine('SYSTEM', 'Connected to AION OS detection engine', 'success');
			send({ action: 'get_stats' });
		};

		ws.onclose = () => {
			const wasOpen = !isConnecting;
			isConnecting = false;
			connectionStatus.set('offline');
			if (wasOpen && reconnectAttempts < MAX_RECONNECT) {
				reconnectAttempts++;
				setTimeout(connect, 3000);
			}
		};

		ws.onerror = () => {
			isConnecting = false;
			connectionStatus.set('offline');
		};

		ws.onmessage = (event) => {
			try {
				handleMessage(JSON.parse(event.data));
			} catch {
				/* ignore parse errors */
			}
		};
	} catch {
		isConnecting = false;
		connectionStatus.set('offline');
	}
}

export function send(data: Record<string, unknown>) {
	if (ws && ws.readyState === WebSocket.OPEN) {
		ws.send(JSON.stringify(data));
	}
}

export function triggerAttack(attackId: string) {
	if (ws && ws.readyState === WebSocket.OPEN) {
		send({ action: 'trigger_attack', attack_id: attackId });
	} else {
		connect();
		setTimeout(() => {
			if (ws && ws.readyState === WebSocket.OPEN) {
				send({ action: 'trigger_attack', attack_id: attackId });
			} else {
				runFallback(attackId);
			}
		}, 1500);
	}
}

export function analyzeDocument(text: string, docType?: string, title?: string, parties?: string[]) {
	docAnalysisLoading.set(true);
	currentDocAnalysis.set(null);
	send({
		action: 'analyze_document',
		text,
		doc_type: docType ?? 'other',
		title: title ?? '',
		parties: parties ?? []
	});
}

let voiceToggleDebounce = false;
export function toggleVoice(enabled?: boolean) {
	if (voiceToggleDebounce) return;
	voiceToggleDebounce = true;
	setTimeout(() => { voiceToggleDebounce = false; }, 500);
	send({ action: 'voice_toggle', enabled });
}

// ── Audio Playback (Queue-based, no overlapping) ───────

let currentAudio: HTMLAudioElement | null = null;
const audioQueue: string[] = [];
let isPlaying = false;

async function playNextInQueue() {
	if (isPlaying || audioQueue.length === 0) return;
	
	isPlaying = true;
	const base64Audio = audioQueue.shift()!;
	console.log('🔊 Playing audio:', base64Audio.length, 'chars, queue remaining:', audioQueue.length);
	
	try {
		// Stop any currently playing audio
		if (currentAudio) {
			currentAudio.pause();
			currentAudio = null;
		}
		
		// Decode base64 to ArrayBuffer
		const binaryString = atob(base64Audio);
		const bytes = new Uint8Array(binaryString.length);
		for (let i = 0; i < binaryString.length; i++) {
			bytes[i] = binaryString.charCodeAt(i);
		}

		// Create audio blob and play via HTML5 Audio
		const blob = new Blob([bytes], { type: 'audio/mpeg' });
		const url = URL.createObjectURL(blob);
		const audio = new Audio(url);
		currentAudio = audio;
		
		audio.onended = () => {
			console.log('🔊 Audio ended, playing next');
			URL.revokeObjectURL(url);
			currentAudio = null;
			isPlaying = false;
			// Play next in queue
			playNextInQueue();
		};
		
		audio.onerror = (e) => {
			console.error('🔊 Audio error:', e);
			URL.revokeObjectURL(url);
			currentAudio = null;
			isPlaying = false;
			playNextInQueue();
		};
		
		await audio.play();
		console.log('🔊 Audio started playing');
	} catch (e) {
		console.warn('🔊 Failed to play audio:', e);
		isPlaying = false;
		playNextInQueue();
	}
}

function queueAudio(base64Audio: string) {
	console.log('🔊 Queuing audio:', base64Audio.length, 'chars');
	audioQueue.push(base64Audio);
	playNextInQueue();
}

// ── Message Router ─────────────────────────────────────

function handleMessage(data: Record<string, unknown>) {
	switch (data.type) {
		case 'connected':
			if (data.stats) handleStats(data.stats as Record<string, unknown>);
			break;
		case 'stats':
			handleStats(data.stats as Record<string, unknown>);
			break;
		case 'scenario_start':
			addLine('▶ SCENARIO', data.name as string, 'scenario');
			addLine('INFO', data.description as string, 'info');
			activeAttack.set(data.attack_id as string);
			currentReport.set(null);
			reportLoading.set(false);
			break;
		case 'event': {
			const time = new Date(data.timestamp as string).toLocaleTimeString();
			const user = (data.user as string).split('@')[0];
			addLine(time, `${data.event_type} ← ${user}`, 'event');
			break;
		}
		case 'alert':
			addLine('█ ALERT', `${data.pattern} [${data.severity}]`, 'alert');
			triggerShake();
			break;
		case 'scenario_complete': {
			const detected = data.detected as boolean;
			addLine(
				'◼ COMPLETE',
				detected ? 'THREAT DETECTED ✓' : 'Monitoring...',
				detected ? 'success' : 'info'
			);
			break;
		}
		case 'detection_summary':
			addLine('⚡ DETECTED', `Pattern matched in ${data.latency_ms}ms — ${data.alerts_generated} alert(s)`, 'success');
			break;
		case 'analysis_start':
			reportLoading.set(true);
			addLine('🧠 SOVEREIGN AI', `Analyzing via ${data.model}...`, 'analysis');
			break;
		case 'analysis_complete':
			reportLoading.set(false);
			currentReport.set(data.analysis as any);
			addLine('', '─'.repeat(50), 'divider');
			activeAttack.set(null);
			break;
		case 'error':
			addLine('ERROR', data.message as string, 'error');
			activeAttack.set(null);
			docAnalysisLoading.set(false);
			break;
		case 'doc_analysis_start':
			docAnalysisLoading.set(true);
			addLine('📄 DOC INTEL', `Analyzing: ${data.title}`, 'analysis');
			break;
		case 'doc_analysis_complete':
			docAnalysisLoading.set(false);
			currentDocAnalysis.set(data as unknown as DocumentAnalysisResult);
			addLine('📄 COMPLETE', `Risk: ${data.risk_score}/100 — ${(data.overall_risk as string).toUpperCase()}`, 'alert');
			break;
		case 'document_list':
			addLine('📄 DOCS', `${data.count} documents in store`, 'info');
			break;
		case 'voice_state':
			voiceEnabled.set(data.enabled as boolean);
			addLine('🔊 VOICE', data.enabled ? 'Voice synthesis enabled' : 'Voice synthesis disabled', 'info');
			break;
		case 'voice_audio':
			if (data.audio) {
				queueAudio(data.audio as string);
			}
			break;
	}
}

function handleStats(s: Record<string, unknown>) {
	stats.set({
		detectionRate: String(s.detection_rate ?? '0'),
		patterns: (s.patterns_loaded as number) ?? 0,
		categories: (s.categories as number) ?? 0,
		latencyMs: (s.latency_ms as number) ?? 0,
		eventsProcessed: (s.events_processed as number) ?? 0,
		alertsGenerated: (s.alerts_generated as number) ?? 0
	});
}

// ── Fallback Simulation ────────────────────────────────

function runFallback(attackId: string) {
	addLine('SYSTEM', 'Running in demo mode (backend offline)', 'info');
	activeAttack.set(attackId);

	const sequence = fallbackScenarios[attackId] ?? Object.values(fallbackScenarios).flat();
	let i = 0;

	function showNext() {
		if (i >= sequence.length) {
			currentReport.set({
				vulnerabilities: [
					{
						title: 'Simulated Threat Analysis',
						severity: 'critical',
						description: 'Demo mode — connect LM Studio for real sovereign AI analysis',
						attack_vector:
							'Pattern detected by rule engine, LLM generates full forensic report',
						countermeasures: [
							'Start LM Studio for live analysis',
							'Run showcase_server.py for full integration'
						]
					}
				],
				risk_score: 92,
				immediate_actions: [
					'Enable LM Studio on localhost:1234',
					'Run: python showcase_server.py'
				],
				latency_ms: 0,
				model: 'demo-mode'
			});
			addLine('', '─'.repeat(50), 'divider');
			activeAttack.set(null);
			return;
		}
		const item = sequence[i];
		addLine(item.prefix, item.text, item.type as any);
		if (item.type === 'alert') triggerShake();
		i++;
		setTimeout(showNext, item.type === 'alert' ? 1500 : 800);
	}

	showNext();
}
