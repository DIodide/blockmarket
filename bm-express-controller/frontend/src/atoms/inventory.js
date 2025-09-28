import { atom } from 'jotai';

// Atom to store inventories for all selected cells
// Structure: Map<cellKey, {diamond: number, gold: number, apple: number, emerald: number, redstone: number}>
export const inventoriesAtom = atom(new Map());
