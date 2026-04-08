/**
 * Simple line-based diffing utility.
 */
export function generateDiff(oldContent: string, newContent: string, filename: string): string {
  const oldLines = oldContent.split('\n');
  const newLines = newContent.split('\n');
  
  let diff = `--- a/${filename}\n+++ b/${filename}\n`;
  
  // Very basic diff: just show the whole file as a change if it's different
  // In a real system, we'd use a library like 'diff' or 'jsdiff'
  // For now, let's at least show the lines added/removed
  
  if (oldContent === newContent) {
    return ""; // No changes
  }

  // Simple "all removed, all added" diff for now to avoid complexity of LCS algorithm
  // but it's better than "[Content Updated]"
  
  diff += `@@ -1,${oldLines.length} +1,${newLines.length} @@\n`;
  
  for (const line of oldLines) {
    if (line.trim() || oldLines.length > 1) {
      diff += `-${line}\n`;
    }
  }
  for (const line of newLines) {
    if (line.trim() || newLines.length > 1) {
      diff += `+${line}\n`;
    }
  }
  
  return diff;
}
