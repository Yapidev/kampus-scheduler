const PALETTES = [
  "bg-blue-50 border-blue-200 text-blue-950",
  "bg-emerald-50 border-emerald-200 text-emerald-950",
  "bg-violet-50 border-violet-200 text-violet-950",
  "bg-amber-50 border-amber-200 text-amber-950",
  "bg-rose-50 border-rose-200 text-rose-950",
  "bg-cyan-50 border-cyan-200 text-cyan-950",
  "bg-indigo-50 border-indigo-200 text-indigo-950",
  "bg-teal-50 border-teal-200 text-teal-950",
];

export function courseCardColor(code: string): string {
  let hash = 0;
  for (let i = 0; i < code.length; i += 1) {
    hash = (hash * 31 + code.charCodeAt(i)) >>> 0;
  }
  return PALETTES[hash % PALETTES.length];
}

export function roomStatusBadge(status: string): string {
  switch (status) {
    case "Optimal":
      return "bg-emerald-100 text-emerald-800 border-emerald-200";
    case "High Load":
      return "bg-amber-100 text-amber-800 border-amber-200";
    case "Oversized Match":
      return "bg-rose-100 text-rose-800 border-rose-200";
    case "Underutilized":
      return "bg-sky-100 text-sky-800 border-sky-200";
    default:
      return "bg-slate-100 text-slate-600 border-slate-200";
  }
}
