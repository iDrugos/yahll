---
name: algorithm-reference
description: Use when implementing, studying, or explaining classical algorithms and data structures in Python, Java, or JavaScript for interviews or learning.
---

# Algorithm Reference

## Overview
Educational implementations of algorithms and data structures across Python, Java, and JavaScript. All implementations prioritize clarity over performance.

## Important Disclaimer
These implementations are for **learning only**. For production use, rely on standard library implementations which are optimized and battle-tested.

## Categories

### Sorting
| Algorithm | Time (avg) | Space | Stable? |
|-----------|-----------|-------|---------|
| Bubble Sort | O(n²) | O(1) | Yes |
| Merge Sort | O(n log n) | O(n) | Yes |
| Quick Sort | O(n log n) | O(log n) | No |
| Heap Sort | O(n log n) | O(1) | No |
| Counting Sort | O(n+k) | O(k) | Yes |

### Searching
| Algorithm | Time | Prerequisite |
|-----------|------|-------------|
| Linear Search | O(n) | None |
| Binary Search | O(log n) | Sorted array |
| BFS | O(V+E) | Graph |
| DFS | O(V+E) | Graph |

### Data Structures
- **Arrays & Strings**: Two-pointer, sliding window
- **Linked Lists**: Fast/slow pointer, reversal
- **Trees**: Traversal (in/pre/post/level), BST, Trie
- **Graphs**: BFS, DFS, Dijkstra, Topological sort
- **Heaps**: Min/max heap, priority queue
- **Hash Tables**: Collision handling

### Dynamic Programming
- Memoization vs Tabulation
- 0/1 Knapsack, LCS, LIS
- Matrix chain multiplication

## Quick Implementation Patterns

```python
# Binary Search
def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target: return mid
        elif arr[mid] < target: lo = mid + 1
        else: hi = mid - 1
    return -1

# BFS
from collections import deque
def bfs(graph, start):
    visited, queue = {start}, deque([start])
    while queue:
        node = queue.popleft()
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return visited
```

## Interview Complexity Cheatsheet
- Hash map lookup: O(1)
- Binary search: O(log n)
- Sorting: O(n log n)
- BFS/DFS: O(V + E)
- DP (grid n×m): O(n×m)

## References
- [TheAlgorithms/Python](https://github.com/TheAlgorithms/Python) — 219K stars
- [TheAlgorithms/Java](https://github.com/TheAlgorithms/Java) — 65K stars
- [TheAlgorithms/JavaScript](https://github.com/TheAlgorithms/JavaScript) — 34K stars
