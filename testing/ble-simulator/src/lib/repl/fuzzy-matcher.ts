import fuzzysort from "fuzzysort";

export class FuzzyMatcher {
  findSimilar(
    input: string,
    targets: string[],
    maxResults: number = 3,
    threshold: number = -1000
  ): string[] {
    if (targets.length === 0) return [];

    const results = fuzzysort.go(input, targets, {
      limit: maxResults,
      threshold: threshold,
    });

    return results.map((result) => result.target);
  }

  findSimilarCharacteristics(
    input: string,
    characteristics: string[]
  ): string[] {
    return this.findSimilar(input, characteristics);
  }

  findSimilarDevices(input: string, devices: string[]): string[] {
    return this.findSimilar(input, devices);
  }

  findSimilarCommands(input: string, commands: string[]): string[] {
    return this.findSimilar(input, commands);
  }
}
