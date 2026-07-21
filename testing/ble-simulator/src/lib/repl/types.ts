export interface Command {
  description: string;
  usage?: string;
  handler?: (args: string[]) => Promise<void> | void;
}

export interface SuggestionResult {
  target: string;
  score: number;
}
