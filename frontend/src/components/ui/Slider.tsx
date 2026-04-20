interface SliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (value: number) => void;
  id: string;
}

export function Slider({
  label,
  value,
  min,
  max,
  step = 1,
  onChange,
  id,
}: SliderProps) {
  return (
    <div className="ui-slider">
      <label className="ui-slider__label" htmlFor={id}>
        <span>{label}</span>
        <span>{value}</span>
      </label>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  );
}
