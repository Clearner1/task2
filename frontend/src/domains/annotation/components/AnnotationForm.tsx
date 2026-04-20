import { Slider, TextArea } from '@ui/index';
import { PRIMARY_EMOTIONS } from '@foundation/types';
import type { AnnotationPayload } from '@foundation/types';
import '../annotation.css';

interface AnnotationFormProps {
  value: AnnotationPayload;
  onChange: (partial: Partial<AnnotationPayload>) => void;
}

export function AnnotationForm({ value, onChange }: AnnotationFormProps) {
  return (
    <div className="annotation-form">
      {/* Primary emotion */}
      <div className="annotation-form__section-title">Primary Emotion</div>
      <div className="annotation-form__emotion-grid">
        {PRIMARY_EMOTIONS.map((e) => (
          <button
            key={e.value}
            type="button"
            className={`emotion-chip ${value.primary_emotion === e.value ? 'emotion-chip--selected' : ''}`}
            onClick={() => onChange({ primary_emotion: e.value })}
            id={`emotion-${e.value}`}
          >
            {e.label}
          </button>
        ))}
      </div>

      {/* Intensity */}
      <Slider
        id="slider-intensity"
        label="Intensity"
        value={value.intensity}
        min={1}
        max={5}
        onChange={(v) => onChange({ intensity: v })}
      />

      {/* Confidence */}
      <Slider
        id="slider-confidence"
        label="Confidence"
        value={value.confidence}
        min={1}
        max={5}
        onChange={(v) => onChange({ confidence: v })}
      />

      {/* Valence */}
      <Slider
        id="slider-valence"
        label="Valence"
        value={value.valence}
        min={-1}
        max={1}
        step={0.1}
        onChange={(v) => onChange({ valence: Math.round(v * 10) / 10 })}
      />

      {/* Arousal */}
      <Slider
        id="slider-arousal"
        label="Arousal"
        value={value.arousal}
        min={1}
        max={5}
        onChange={(v) => onChange({ arousal: v })}
      />

      {/* Notes */}
      <TextArea
        id="annotation-notes"
        label="Notes"
        value={value.notes}
        onChange={(v) => onChange({ notes: v })}
        placeholder="Add observation notes..."
        rows={3}
      />
    </div>
  );
}
