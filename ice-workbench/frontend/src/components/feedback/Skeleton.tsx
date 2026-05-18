import "./ErrorState.css";

export function Skeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div>
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className={"skel-line" + (i % 2 === 1 ? " short" : "")} />
      ))}
    </div>
  );
}
