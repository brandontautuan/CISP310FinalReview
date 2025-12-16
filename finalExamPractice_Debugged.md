# Final Exam Practice - Debugged and Fully Commented

## Debugging Methodology

When debugging TTPASM code, follow these systematic steps:

1. **Understand the C Code**: Start by reading the C code to understand what the program should do
2. **Trace the Stack**: Draw the stack frame layout for each function, tracking where parameters and locals are
3. **Follow Register Values**: For each instruction, track what value each register contains
4. **Verify Parameter Access**: Check that parameters are accessed using correct offsets from stack pointer
5. **Check Stack Balance**: Ensure pushes match pops, and caller/callee responsibilities are met
6. **Verify Control Flow**: Trace through if/while loops to ensure logic matches C code
7. **Check Type Sizes**: Verify offsets account for correct sizes (1 byte for pointers, not struct sizes)
8. **Review Register Usage**: Ensure registers aren't overwritten before their values are used

## Key Principles Applied

- **Stack grows downward**: Pushing decrements D, popping increments D
- **Parameters are at positive offsets** from where D points at function entry
- **Local variables are at base** (D+0) after allocation
- **Arguments pushed in reverse order**: Last argument first, first argument last
- **Caller cleans arguments, callee cleans return address**
- **Struct members have fixed offsets** from struct base address
- **Pointers are 1 byte** in TTPASM, not the size of what they point to

---

## Bug Analysis and Fixes

This document contains the debugged version of the assembly code with detailed comments explaining each line and the thought process behind bug fixes.

---

## BUG 1: Line 60 - Missing Stack Pointer Initialization
**Issue**: `ldi d,` has no value, cannot initialize stack pointer
**Fix**: `ldi d, 0` to initialize stack pointer to 0

## BUG 2: Line 107 - Wrong Offset Calculation for result
**Issue**: `isLoop_result: isLoop_fPtr Node_size +` uses `Node_size` (2 bytes) when `fPtr` is a pointer (1 byte)
**Fix**: `isLoop_result: isLoop_fPtr 1 +` since pointers are 1 byte in TTPASM

## BUG 3: Line 112 - Incorrect Local Variable Allocation Syntax
**Issue**: `ldi c,0 isLoop_lvs -` is invalid syntax - cannot subtract in ldi
**Fix**: `ldi c, isLoop_lvs` then `sub d, c` to allocate locals

## BUG 4: Lines 119-121 - Incorrect Parameter Access
**Issue**: Loading `pNode` incorrectly - `ld a,(a)` tries to dereference the offset, not the parameter
**Fix**: Must compute address of parameter first: `ldi a, isLoop_pNode` then `add a, d` then `ld a, (a)`

## BUG 5: Lines 124-129 - Incorrect prevFrame Assignment to f.prevFrame
**Issue**: Complex incorrect calculation with `Frame_prevFrame Frame_pNode -` which is wrong
**Fix**: Simply load prevFrame parameter and store to f.prevFrame

## BUG 6: Lines 136-137 - Wrong Way to Access Parameter prevFrame
**Issue**: Using `Frame_prevFrame` (struct member offset) instead of parameter offset `isLoop_prevFrame`
**Fix**: Use `ldi a, isLoop_prevFrame` then `add a, d` then `ld a, (a)`

## BUG 7: Line 169 - Wrong Register Used to Store fPtr
**Issue**: `st (c),b` - register `c` doesn't contain the address of fPtr here
**Fix**: Must recompute address: `ldi c, isLoop_fPtr` then `add c, d` then `st (c), b`

## BUG 8: Line 172 - Register c May Not Contain fPtr
**Issue**: `and c,c` tests register c, but c was last used for saving/restoring and may not contain fPtr
**Fix**: Must reload fPtr: `ldi c, isLoop_fPtr` then `add c, d` then `ld c, (c)` then test

## BUG 9: Line 197 - Wrong Register Contains Result
**Issue**: `st (b),c` - register c may not contain the OR result
**Fix**: After OR logic, result should be in a specific register, then store it

## BUG 10: Line 182 - Wrong Offset for Parameter
**Issue**: `ldi b,isLoop_pNode 1 +` - adding 1 doesn't skip return address properly
**Fix**: Should use `isLoop_pNode` directly since it already accounts for local vars + ret addr

## BUG 11: Line 218 - Missing Value for Second Argument
**Issue**: `ldi a,` has no value for pushing prevFrame argument (should be 0)
**Fix**: `ldi a, 0`

## BUG 12: Line 232 - Missing Value for Argument Cleanup
**Issue**: `ldi b,` has no value for cleaning up 2 arguments
**Fix**: `ldi b, 2` then `add d, b` or use two `inc d` instructions

## BUG 13: Line 199 - Wrong Label Name
**Issue**: Label is `isLoop_endif0` but jump at line 132 goes to `isLoop_endif`
**Fix**: Should be consistent - use `isLoop_endif`

---

## FULLY DEBUGGED CODE WITH COMMENTS

```assembly
// ============================================================================
// PROGRAM INITIALIZATION
// ============================================================================

nop
// BUG FIX 1: Initialize stack pointer D to 0
// THINKING: Stack pointer must be initialized before use
// Original bug: ldi d, (missing value)
ldi d, 0        // D = 0 (initialize stack pointer to address 0)
dec d           // D = D - 1 (reserve space for initial stack item)
ldi b, . 6 +    // B = PC + 6 (compute return address - 6 instructions ahead)
st (d), b       // *D = B (store return address on stack)
// THINKING: Return address points to instruction after jmpi main

jmpi main       // Jump to main function
halt            // Halt execution (should never reach here if main returns)

// ============================================================================
// DATA STRUCTURE DEFINITIONS
// ============================================================================

// struct Node {
//     void *payload;      // 1 byte (pointer in TTPASM)
//     struct Node *pNext; // 1 byte (pointer in TTPASM)
// };
// Total size: 2 bytes

Node_payload: 0              // Offset 0: payload member
Node_pNext: Node_payload 1 + // Offset 1: pNext member (0 + 1 = 1)
Node_size: Node_pNext 1 +    // Total size: 2 bytes (1 + 1 = 2)

// struct Frame {
//     struct Node *pNode;      // 1 byte (pointer)
//     struct Frame *prevFrame; // 1 byte (pointer)
// };
// Total size: 2 bytes

Frame_pNode: 0                    // Offset 0: pNode member
Frame_prevFrame: Frame_pNode 1 +  // Offset 1: prevFrame member (0 + 1 = 1)
Frame_size: Frame_prevFrame 1 +   // Total size: 2 bytes (1 + 1 = 2)

// struct Node circle[] = {
//     { 0, &circle[1] },  // circle[0]: payload=0, pNext=&circle[1]
//     { 0, &circle[2] },  // circle[1]: payload=0, pNext=&circle[2]
//     { 0, &circle[0] }   // circle[2]: payload=0, pNext=&circle[0]
// };
// Forms a cycle: 0 -> 1 -> 2 -> 0

circle:
    byte 0                           // circle[0].payload = 0
    byte circle 1 Node_size * +      // circle[0].pNext = &circle[1] = circle + (1 * 2) = circle + 2
    byte 0                           // circle[1].payload = 0
    byte circle 2 Node_size * +      // circle[1].pNext = &circle[2] = circle + (2 * 2) = circle + 4
    byte 0                           // circle[2].payload = 0
    byte circle 0 Node_size * +      // circle[2].pNext = &circle[0] = circle + (0 * 2) = circle

// ============================================================================
// FUNCTION: isLoop
// ============================================================================
// C Code:
// uint8_t isLoop(struct Node *pNode, struct Frame *prevFrame) {
//     struct Frame f;
//     struct Frame *fPtr;
//     uint8_t result;
//     result = 0;
//     f.pNode = pNode;
//     f.prevFrame = prevFrame;
//     if (pNode) {
//         fPtr = prevFrame;
//         while (fPtr && (fPtr->pNode != pNode)) {
//             fPtr = fPtr->prevFrame;
//         }
//         result = (fPtr != 0) || isLoop(pNode->pNext, &f);
//     }
//     return result;
// }

isLoop:
    // ========================================================================
    // FRAME LAYOUT DEFINITION
    // ========================================================================
    // At function entry, stack looks like:
    //   D+2: prevFrame (parameter 2)
    //   D+1: pNode (parameter 1)
    //   D+0: return address
    //
    // After allocating locals (4 bytes total):
    //   D+6: prevFrame (parameter 2)
    //   D+5: pNode (parameter 1)
    //   D+4: return address
    //   D+3: fPtr (local variable, 1 byte)
    //   D+2: result (local variable, 1 byte)
    //   D+1: f.prevFrame (member of struct Frame f)
    //   D+0: f.pNode (member of struct Frame f) ← D points here
    
    isLoop_f: 0                        // Offset to struct Frame f (starts at base)
    isLoop_fPtr: isLoop_f Frame_size + // Offset to fPtr = 0 + 2 = 2
    // BUG FIX 2: fPtr is a pointer (1 byte), not a Node, so use 1+ not Node_size+
    isLoop_result: isLoop_fPtr 1 +     // Offset to result = 2 + 1 = 3
    isLoop_lvs: isLoop_result 1 +      // Local variable size = 3 + 1 = 4 bytes
    isLoop_pNode: isLoop_lvs 1 +       // Offset to pNode parameter = 4 + 1 = 5
    isLoop_prevFrame: isLoop_pNode 1 + // Offset to prevFrame parameter = 5 + 1 = 6

    // ========================================================================
    // ALLOCATE LOCAL VARIABLES
    // ========================================================================
    // BUG FIX 3: Correct syntax for allocation
    // Original bug: ldi c,0 isLoop_lvs - (invalid syntax)
    // THINKING: Need to subtract local var size from stack pointer
    ldi c, isLoop_lvs  // C = 4 (size of local variables)
    sub d, c            // D = D - 4 (allocate 4 bytes for local variables)
    // THINKING: D now points to base of frame where f.pNode will be stored

    // ========================================================================
    // result = 0;
    // ========================================================================
    sub a, a            // A = 0 (set result to 0 using subtraction trick)
    ldi b, isLoop_result // B = 3 (offset to result variable)
    add b, d            // B = D + 3 (address of result variable)
    st (b), a           // *B = A, i.e., result = 0

    // ========================================================================
    // f.pNode = pNode;
    // ========================================================================
    // BUG FIX 4: Correctly access parameter pNode
    // Original bug: ldi a,isLoop_pNode then ld a,(a) - tries to dereference offset!
    // THINKING: Must compute address of parameter on stack first
    ldi a, isLoop_pNode // A = 5 (offset to pNode parameter)
    add a, d            // A = D + 5 (address of pNode parameter on stack)
    ld a, (a)           // A = *(D+5) = pNode (value of parameter)
    
    // Now store to f.pNode
    ldi b, isLoop_f     // B = 0 (offset to f.pNode, which is Frame_pNode offset)
    add b, Frame_pNode  // B = 0 + 0 = 0 (Frame_pNode is 0, so B = offset to f.pNode)
    add b, d            // B = D + 0 (address of f.pNode)
    st (b), a           // *B = A, i.e., f.pNode = pNode

    // ========================================================================
    // f.prevFrame = prevFrame;
    // ========================================================================
    // BUG FIX 5: Correctly load prevFrame parameter and store to f.prevFrame
    // Original bug: Complex incorrect calculation with Frame_prevFrame Frame_pNode -
    // THINKING: Simply load parameter and store to struct member
    ldi a, isLoop_prevFrame // A = 6 (offset to prevFrame parameter)
    add a, d                // A = D + 6 (address of prevFrame parameter)
    ld a, (a)               // A = *(D+6) = prevFrame (value of parameter)
    
    // Store to f.prevFrame
    ldi b, isLoop_f         // B = 0 (base offset of struct f)
    add b, Frame_prevFrame  // B = 0 + 1 = 1 (offset to f.prevFrame)
    add b, d                // B = D + 1 (address of f.prevFrame)
    st (b), a               // *B = A, i.e., f.prevFrame = prevFrame

    // ========================================================================
    // if (pNode) {
    // ========================================================================
    ldi a, isLoop_pNode // A = 5 (offset to pNode parameter)
    add a, d            // A = D + 5 (address of pNode parameter)
    ld a, (a)           // A = pNode (value of parameter)
    and a, a            // A = A & A (sets Z flag if A == 0, doesn't change A)
    // THINKING: Z flag set if pNode == 0 (null pointer)
    jzi isLoop_endif    // If pNode == 0, skip the if block
    // BUG FIX 13: Label should be isLoop_endif not isLoop_endif0

    // ========================================================================
    // fPtr = prevFrame;
    // ========================================================================
    // BUG FIX 6: Correctly access prevFrame parameter
    // Original bug: ldi a,Frame_prevFrame then ld a,(a) - wrong! That's struct member offset
    // THINKING: Must use parameter offset isLoop_prevFrame, not struct member offset
    ldi a, isLoop_prevFrame // A = 6 (offset to prevFrame parameter)
    add a, d                // A = D + 6 (address of prevFrame parameter)
    ld a, (a)               // A = *(D+6) = prevFrame (value of parameter)
    
    // Store to fPtr
    ldi b, isLoop_fPtr      // B = 2 (offset to fPtr local variable)
    add b, d                // B = D + 2 (address of fPtr)
    st (b), a               // *B = A, i.e., fPtr = prevFrame

    // ========================================================================
    // while (fPtr && (fPtr->pNode != pNode)) {
    // ========================================================================
    isLoop_then0_while0_begin:
        // ====================================================================
        // MANDATORY REGISTER DOCUMENTATION (as per exam requirements)
        // ====================================================================
        
        // Load fPtr and check if it's null
        ldi c, isLoop_fPtr  // C = 2 (offset to fPtr variable)
        add c, d            // C = D + 2 (address of fPtr) ← C contains address
        ld b, (c)           // B = *(D+2) = fPtr (value of fPtr variable) ← B contains fPtr value
        // THINKING: Register B now contains the value of fPtr from C code
        
        and b, b            // B = B & B (sets Z flag if B == 0, doesn't change B)
        // THINKING: Z flag set if fPtr == 0 (null pointer check)
        jzi isLoop_then0_while0_end // If fPtr == 0, exit while loop
        
        // Compute fPtr->pNode
        ldi a, Frame_pNode  // A = 0 (offset to pNode member in Frame struct)
        add b, a            // B = fPtr + 0 (address of fPtr->pNode)
        // THINKING: Register B now contains address of fPtr->pNode member
        ld a, (b)           // A = *(fPtr->pNode) = fPtr->pNode (value of pNode member)
        // THINKING: Register A now contains fPtr->pNode from C code
        
        // Save register C (contains address of fPtr) on stack for later use
        // THINKING: We need to preserve C because we'll use it to store back to fPtr later
        dec d               // D = D - 1 (reserve space on stack)
        st (d), c           // *D = C (save address of fPtr variable on stack)
        // THINKING: After push, frame layout shifts:
        //   Before: D points to frame base (f.pNode at D+0)
        //   After:  D points to saved C, frame base at D+1, pNode param at D+6
        
        // Load pNode parameter for comparison
        // BUG: Original code uses ldi c,Frame_pNode 1 + which is 1, then add c,d
        // This gives D+1, which is f.prevFrame, NOT pNode parameter!
        // CORRECT FIX: Use isLoop_pNode offset (5) and adjust for the push (+1)
        ldi c, isLoop_pNode // C = 5 (offset to pNode from original frame base)
        inc c                // C = 6 (adjust: frame base moved from D+0 to D+1 due to push)
        add c, d             // C = D + 6 (address of pNode parameter)
        ld c, (c)            // C = *(D+6) = pNode (value of parameter)
        // THINKING: Register C now contains pNode parameter value for comparison
        
        // Restore saved address of fPtr variable from stack
        ld b, (d)            // B = *D = address of fPtr variable (restored from stack)
        inc d                // D = D + 1 (deallocate stack space, restore to frame base)
        // THINKING: D is back to frame base, B contains address where fPtr is stored
        
        // Compare: fPtr->pNode != pNode
        // Register A contains fPtr->pNode (from line 152)
        // Register C contains pNode (parameter value)
        cmp a, c             // Compute A - C (fPtr->pNode - pNode), sets Z flag if equal
        // THINKING: Z flag is set if fPtr->pNode == pNode
        // While condition: fPtr && (fPtr->pNode != pNode)
        // We exit loop when fPtr->pNode == pNode (i.e., when Z flag is set)
        jzi isLoop_then0_while0_end // If fPtr->pNode == pNode, exit loop
        
        // ====================================================================
        // fPtr = fPtr->prevFrame;
        // ====================================================================
        // Register B currently contains address of fPtr variable
        // We need the VALUE of fPtr to access fPtr->prevFrame
        // BUG: Original code at line 168 does ld b,(b) which overwrites B
        // but then tries to compute offset using the wrong register
        // Let's use a temporary register approach:
        
        // First, get the value of fPtr into a register
        ld c, (b)            // C = *B = fPtr (value of fPtr variable, where B is address)
        // THINKING: Register C now contains fPtr (pointer value) from C code
        // Register B still contains address of fPtr variable (needed for later store)
        
        // Compute fPtr->prevFrame
        // BUG FIX 7: Original code computes Frame_prevFrame Frame_pNode - which is 1-0=1
        // That's correct, but the way it uses registers is wrong
        ldi a, Frame_prevFrame // A = 1 (offset to prevFrame member in Frame struct)
        add c, a              // C = fPtr + 1 (address of fPtr->prevFrame member)
        ld c, (c)             // C = *(fPtr->prevFrame) = fPtr->prevFrame (new value)
        // THINKING: Register C now contains fPtr->prevFrame (the new fPtr value)
        
        // Store back to fPtr variable
        // Register B still contains the address of fPtr variable (from earlier)
        st (b), c            // *B = C, i.e., fPtr = fPtr->prevFrame
        // THINKING: fPtr variable is updated with its prevFrame value
        
        jmpi isLoop_then0_while0_begin // Loop back to beginning

    isLoop_then0_while0_end:

    // ========================================================================
    // result = (fPtr != 0) || isLoop(pNode->pNext, &f);
    // ========================================================================
    // This implements: result = fPtr != 0 ? 1 : isLoop(pNode->pNext, &f)
    // Using OR short-circuit: if fPtr != 0, result = 1, else evaluate isLoop
    
    // BUG FIX 8: Register c may not contain fPtr - must reload it
    // Original bug: and c,c - but c was last used for something else
    ldi c, isLoop_fPtr      // C = 2 (offset to fPtr variable)
    add c, d                // C = D + 2 (address of fPtr variable)
    ld c, (c)               // C = *(D+2) = fPtr (value of fPtr variable)
    // THINKING: Register C now contains fPtr value for the comparison
    
    and c, c                // C = C & C (sets Z flag if C == 0)
    // THINKING: Z flag set if fPtr == 0
    jzi isLoop_then0_orElse // If fPtr == 0, evaluate right side of OR
    // If fPtr != 0, short-circuit: result = 1 (true)
    ldi c, 1                // C = 1 (result = true)
    jmpi isLoop_then0_orDone // Skip recursive call

    isLoop_then0_orElse:
        // Evaluate isLoop(pNode->pNext, &f)
        // Push &f (address of local struct f) as second argument
        ldi c, isLoop_f     // C = 0 (offset to struct f)
        add c, d            // C = D + 0 (address of struct f, i.e., &f)
        dec d               // D = D - 1 (reserve space for argument)
        st (d), c           // *D = C, push &f (second argument)
        
        // Compute pNode->pNext
        // BUG FIX 10: Wrong offset calculation
        // Original bug: ldi b,isLoop_pNode 1 + which is 5+1=6
        // But after the push, pNode is at a different offset
        // Let me recalculate: pNode was at D+5 before, now after push it's at D+6
        ldi b, isLoop_pNode // B = 5 (offset to pNode parameter from frame base)
        inc b                // B = 6 (adjust for the push we just did)
        add b, d             // B = D + 6 (address of pNode parameter)
        ld b, (b)            // B = *(D+6) = pNode (value of parameter)
        // THINKING: Register B now contains pNode (pointer to Node)
        
        // Compute pNode->pNext
        ldi a, Node_pNext   // A = 1 (offset to pNext member in Node struct)
        add b, a            // B = pNode + 1 (address of pNode->pNext)
        ld b, (b)           // B = *(pNode->pNext) = pNode->pNext (value)
        // THINKING: Register B now contains pNode->pNext from C code
        
        // Push pNode->pNext as first argument
        dec d               // D = D - 1 (reserve space for argument)
        st (d), b           // *D = B, push pNode->pNext (first argument)
        
        // Push return address
        ldi a, . 6 +        // A = PC + 6 (return address)
        dec d               // D = D - 1 (reserve space for return address)
        st (d), a           // *D = A, push return address
        
        // Call isLoop recursively
        jmpi isLoop
        
        // After return: A contains return value (result of recursive call)
        // Clean up arguments (2 arguments: pNode->pNext and &f)
        inc d               // Deallocate first argument (pNode->pNext)
        inc d               // Deallocate second argument (&f)
        
        // Return value is in A, but we need it in C for the OR result
        cpr c, a            // C = A (result of recursive call)
        // THINKING: Register C now contains the result of isLoop(pNode->pNext, &f)

    isLoop_then0_orDone:
        // Store result: C contains 1 if fPtr != 0, or result of recursive call
        ldi b, isLoop_result // B = 3 (offset to result variable)
        add b, d             // B = D + 3 (address of result variable)
        st (b), c            // *B = C, i.e., result = (fPtr != 0) || isLoop(...)
        // THINKING: Result variable now contains the OR expression result

    isLoop_endif:  // BUG FIX 13: Changed from isLoop_endif0 to isLoop_endif

    // ========================================================================
    // return result;
    // ========================================================================
    ldi a, isLoop_result // A = 3 (offset to result variable)
    add a, d             // A = D + 3 (address of result variable)
    ld a, (a)            // A = *(D+3) = result (value to return)
    // THINKING: Register A now contains result value for return

    // ========================================================================
    // DEALLOCATE LOCAL VARIABLES AND RETURN
    // ========================================================================
    ldi c, isLoop_lvs    // C = 4 (size of local variables)
    add d, c             // D = D + 4 (deallocate local variables)
    // THINKING: D now points to return address
    
    ld c, (d)            // C = *D = return address
    inc d                // D = D + 1 (pop return address from stack)
    jmp c                // Jump to return address (return to caller)

// ============================================================================
// FUNCTION: main
// ============================================================================
// C Code:
// int main() {
//     uint8_t x;
//     x = isLoop(&circle[1], 0);
//     return 0;
// }

main:
    // ========================================================================
    // FRAME LAYOUT
    // ========================================================================
    // After allocating local (1 byte):
    //   D+1: return address (from initial setup)
    //   D+0: x (local variable) ← D points here
    
    main_x: 0              // Offset to local variable x
    main_lvs: main_x 1 +   // Local variable size = 0 + 1 = 1 byte

    // ========================================================================
    // ALLOCATE LOCAL VARIABLE
    // ========================================================================
    ldi b, main_lvs        // B = 1 (size of local variables)
    sub d, b               // D = D - 1 (allocate 1 byte for local variable x)
    // THINKING: D now points to where x will be stored

    // ========================================================================
    // x = isLoop(&circle[1], 0);
    // ========================================================================
    // Call isLoop with arguments: pNode = &circle[1], prevFrame = 0
    // Arguments pushed in reverse order (last argument first)
    
    // Push second argument: prevFrame = 0
    // BUG FIX 11: Missing value - should be 0
    // Original bug: ldi a, (missing value)
    ldi a, 0               // A = 0 (prevFrame argument value)
    dec d                  // D = D - 1 (reserve space for argument)
    st (d), a              // *D = A, push 0 (second argument: prevFrame)
    
    // Push first argument: pNode = &circle[1]
    // Compute &circle[1] = circle + (1 * Node_size) = circle + 2
    ldi a, circle          // A = address of circle[0]
    ldi b, Node_size       // B = 2 (size of one Node element)
    add a, b               // A = circle + 2 = &circle[1]
    // THINKING: Register A now contains &circle[1] (address of circle[1])
    
    dec d                  // D = D - 1 (reserve space for argument)
    st (d), a              // *D = A, push &circle[1] (first argument: pNode)
    
    // Push return address
    ldi a, . 6 +           // A = PC + 6 (return address - 6 instructions ahead)
    dec d                  // D = D - 1 (reserve space for return address)
    st (d), a              // *D = A, push return address
    
    // Call isLoop
    jmpi isLoop
    
    // After return: A contains return value from isLoop
    // Clean up arguments (2 arguments: pNode and prevFrame)
    // BUG FIX 12: Missing value - need to clean up 2 arguments
    // Original bug: ldi b, (missing value) then add d,b
    // Fix: use two inc d instructions
    inc d                  // Deallocate first argument (pNode)
    inc d                  // Deallocate second argument (prevFrame)
    // THINKING: Stack is now balanced (callee already popped return address)

    // Store return value to x
    ldi b, main_x          // B = 0 (offset to local variable x)
    add b, d               // B = D + 0 (address of x)
    st (b), a              // *B = A, i.e., x = isLoop(&circle[1], 0)
    // THINKING: Local variable x now contains the result

    // ========================================================================
    // return 0;
    // ========================================================================
    sub a, a               // A = 0 (return value)

    // ========================================================================
    // DEALLOCATE LOCAL VARIABLE
    // ========================================================================
    ldi b, main_lvs        // B = 1 (size of local variables)
    add d, b               // D = D + 1 (deallocate local variable x)
    // THINKING: D now points to return address (from initial setup)

    // Return (jump to return address from initial setup)
    ld b, (d)              // B = *D = return address
    jmp b                  // Jump to return address

// End of program
```

---

## SUMMARY OF BUGS FIXED

1. **Line 60**: Added missing value `0` to `ldi d, 0` for stack initialization
2. **Line 107**: Changed `Node_size +` to `1 +` since fPtr is 1 byte, not 2
3. **Line 112**: Fixed allocation syntax from `ldi c,0 isLoop_lvs -` to `ldi c, isLoop_lvs` then `sub d, c`
4. **Lines 119-121**: Fixed parameter access by properly computing address with `add a, d` before `ld a, (a)`
5. **Lines 124-129**: Fixed prevFrame assignment by correctly loading parameter and storing to struct member
6. **Lines 136-137**: Fixed parameter access by using `isLoop_prevFrame` instead of `Frame_prevFrame`
7. **Line 169**: Fixed fPtr update by recomputing address of fPtr variable
8. **Line 172**: Fixed fPtr test by reloading fPtr value before testing
9. **Line 182**: Fixed offset calculation for pNode parameter access in recursive call
10. **Line 197**: Result storage is now correct after fixing register tracking
11. **Line 218**: Added missing value `0` for prevFrame argument
12. **Line 232**: Fixed argument cleanup by using two `inc d` instructions
13. **Line 199**: Fixed label name from `isLoop_endif0` to `isLoop_endif`

---

## KEY CONCEPTS DEMONSTRATED

1. **Stack Frame Management**: Proper allocation/deallocation of local variables
2. **Parameter Access**: Computing addresses using offsets from stack pointer
3. **Struct Member Access**: Using struct member offsets to access nested data
4. **Pointer Dereferencing**: Loading addresses, then dereferencing to get values
5. **Recursive Function Calls**: Proper argument passing and cleanup
6. **Register Tracking**: Maintaining awareness of what each register contains
7. **Stack Balance**: Ensuring stack is balanced after function calls
8. **Control Flow**: Implementing while loops and conditional logic
9. **OR Short-Circuit Evaluation**: Implementing `A || B` with short-circuit
10. **Array Indexing**: Computing addresses for array elements

