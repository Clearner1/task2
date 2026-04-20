import { describe, expect, it } from 'vitest';

import { describePlayableAsset, getMediaAsset, type MediaRecord, TaskStatus } from './index';

const media: MediaRecord = {
  media_id: '1226-141268-0001',
  source_path: 'task2/media/1226-141268-0001.mp3',
  media_type: 'audio',
  detected_format: 'mp3',
  duration_ms: 14670,
  status: TaskStatus.PREPROCESSED,
  failure_reason: null,
  stream_url: '/api/media/1226-141268-0001/stream',
  playable_asset_url: '/api/media/1226-141268-0001/stream',
  waveform_url: '/api/media/1226-141268-0001/waveform',
  poster_url: null,
  assets: [
    {
      asset_kind: 'playable',
      path: 'task2/workspace/normalized/1226-141268-0001/playable.wav',
      format: 'wav',
      sample_rate: 16000,
      channels: 1,
      width: null,
      height: null,
      url: '/api/media/1226-141268-0001/stream',
      created_at: '2026-04-20T10:00:00+08:00',
      updated_at: '2026-04-20T10:00:00+08:00',
    },
    {
      asset_kind: 'waveform',
      path: 'task2/workspace/normalized/1226-141268-0001/waveform.json',
      format: 'json',
      sample_rate: 16000,
      channels: 1,
      width: null,
      height: null,
      url: '/api/media/1226-141268-0001/waveform',
      created_at: '2026-04-20T10:00:00+08:00',
      updated_at: '2026-04-20T10:00:00+08:00',
    },
  ],
  created_at: '2026-04-20T10:00:00+08:00',
  updated_at: '2026-04-20T10:00:00+08:00',
};

describe('media asset helpers', () => {
  it('finds an asset by kind', () => {
    const waveform = getMediaAsset(media, 'waveform');
    expect(waveform?.path).toContain('waveform.json');
  });

  it('describes the playable asset', () => {
    expect(describePlayableAsset(media)).toBe('WAV · 16000 Hz · 1 ch');
  });
});
