interface Props {
  insights: string[] | null;
}

export function InsightsPanel({ insights }: Props) {
  if (!insights?.length) return null;
  return (
    <section className="rounded-xl border border-lab-border bg-lab-panel p-6">
      <h2 className="text-lg font-medium text-white">What did we learn?</h2>
      <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-slate-300">
        {insights.map((line, i) => (
          <li key={i}>{line.replace(/\*\*(.*?)\*\*/g, "$1")}</li>
        ))}
      </ul>
    </section>
  );
}
