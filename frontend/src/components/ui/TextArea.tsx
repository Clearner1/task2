interface TextAreaProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  id: string;
  placeholder?: string;
  rows?: number;
}

export function TextArea({
  label,
  value,
  onChange,
  id,
  placeholder = '',
  rows = 3,
}: TextAreaProps) {
  return (
    <div className="ui-textarea">
      <label className="ui-textarea__label" htmlFor={id}>
        {label}
      </label>
      <textarea
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
      />
    </div>
  );
}
