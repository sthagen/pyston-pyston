//===- Interpreter.cpp - Top-Level LLVM Interpreter Implementation --------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
//
// This file implements the top-level functionality for the LLVM interpreter.
// This interpreter is designed to be a very simple, portable, inefficient
// interpreter.
//
//===----------------------------------------------------------------------===//

#include "Interpreter.h"
#include "llvm/CodeGen/IntrinsicLowering.h"
#include "llvm/IR/DerivedTypes.h"
#include "llvm/IR/Module.h"
#include <cstring>

using namespace llvm;
using namespace nitrous::llvm_interp;

//===----------------------------------------------------------------------===//
// Interpreter ctor - Initialize stuff
//
Interpreter::Interpreter(std::unique_ptr<Module> M)
    : ExecutionEngine(std::move(M)) {

  memset(&ExitValue.Untyped, 0, sizeof(ExitValue.Untyped));
  // Initialize the "backend"
  initializeExecutionEngine();

  IL = new IntrinsicLowering(getDataLayout());
}

Interpreter::~Interpreter() {
  delete IL;
}

void Interpreter::runAtExitHandlers () {
  while (!AtExitHandlers.empty()) {
    callFunction(AtExitHandlers.back(), None);
    AtExitHandlers.pop_back();
    run();
  }
}

/// run - Start execution with the specified function and arguments.
///
GenericValue Interpreter::runFunction(Function *F,
                                      ArrayRef<GenericValue> ArgValues) {
  assert (F && "Function *F was null at entry to run()");

  // Try extra hard not to pass extra args to a function that isn't
  // expecting them.  C programmers frequently bend the rules and
  // declare main() with fewer parameters than it actually gets
  // passed, and the interpreter barfs if you pass a function more
  // parameters than it is declared to take. This does not attempt to
  // take into account gratuitous differences in declared types,
  // though.
  const size_t ArgCount = F->getFunctionType()->getNumParams();
  ArrayRef<GenericValue> ActualArgs =
      ArgValues.slice(0, std::min(ArgValues.size(), ArgCount));

  // Set up the function call.
  callFunction(F, ActualArgs);

  // Start executing the function.
  run();

  return ExitValue;
}
