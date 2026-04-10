export function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

export function setAtPath(root, path, value) {
  const next = clone(root);
  let cursor = next;
  for (let index = 0; index < path.length - 1; index += 1) {
    cursor = cursor[path[index]];
  }
  cursor[path[path.length - 1]] = value;
  return next;
}

export function readAtPath(root, path) {
  return path.reduce((cursor, key) => cursor?.[key], root);
}
