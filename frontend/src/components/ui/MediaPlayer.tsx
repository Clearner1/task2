interface MediaPlayerProps {
  src: string;
  type: 'audio' | 'video';
  label?: string;
  id: string;
}

export function MediaPlayer({ src, type, label, id }: MediaPlayerProps) {
  return (
    <div className="ui-player">
      {label && <div className="ui-player__label">{label}</div>}
      {type === 'audio' ? (
        <audio id={id} src={src} controls preload="metadata" />
      ) : (
        <video id={id} src={src} controls preload="metadata" />
      )}
    </div>
  );
}
