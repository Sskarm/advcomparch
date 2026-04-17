#include "pin.H"

#include <iostream>
#include <fstream>
#include <cassert>

using namespace std;

#include "branch_predictor.h"
#include "pentium_m_predictor/pentium_m_branch_predictor.h"
#include "ras.h"

/* ===================================================================== */
/* Commandline Switches                                                  */
/* ===================================================================== */
KNOB<string> KnobOutputFile(KNOB_MODE_WRITEONCE,    "pintool",
    "o", "cslab_branch.out", "specify output file name");
/* ===================================================================== */

/* ===================================================================== */
/* Global Variables                                                      */
/* ===================================================================== */
std::vector<BranchPredictor *> branch_predictors;
typedef std::vector<BranchPredictor *>::iterator bp_iterator_t;

//> BTBs have slightly different interface (they also have target predictions)
//  so we need to have different vector for them.
std::vector<BTBPredictor *> btb_predictors;
typedef std::vector<BTBPredictor *>::iterator btb_iterator_t;

std::vector<RAS *> ras_vec;
typedef std::vector<RAS *>::iterator ras_vec_iterator_t;

UINT64 total_instructions;
std::ofstream outFile;

/* ===================================================================== */

INT32 Usage()
{
    cerr << "This tool simulates various branch predictors.\n\n";
    cerr << KNOB_BASE::StringKnobSummary();
    cerr << endl;
    return -1;
}

/* ===================================================================== */

VOID count_instruction()
{
    total_instructions++;
}

VOID call_instruction(ADDRINT ip, ADDRINT target, UINT32 ins_size)
{
    ras_vec_iterator_t ras_it;

    for (ras_it = ras_vec.begin(); ras_it != ras_vec.end(); ++ras_it) {
        RAS *ras = *ras_it;
        ras->push_addr(ip + ins_size);
    }
}

VOID ret_instruction(ADDRINT ip, ADDRINT target)
{
    ras_vec_iterator_t ras_it;

    for (ras_it = ras_vec.begin(); ras_it != ras_vec.end(); ++ras_it) {
        RAS *ras = *ras_it;
        ras->pop_addr(target);
    }
}

VOID cond_branch_instruction(ADDRINT ip, ADDRINT target, BOOL taken)
{
    bp_iterator_t bp_it;
    BOOL pred;

    for (bp_it = branch_predictors.begin(); bp_it != branch_predictors.end(); ++bp_it) {
        BranchPredictor *curr_predictor = *bp_it;
        pred = curr_predictor->predict(ip, target);
        curr_predictor->update(pred, taken, ip, target);
    }
}

VOID branch_instruction(ADDRINT ip, ADDRINT target, BOOL taken)
{
    btb_iterator_t btb_it;
    BOOL pred;

    for (btb_it = btb_predictors.begin(); btb_it != btb_predictors.end(); ++btb_it) {
        BTBPredictor *curr_predictor = *btb_it;
        pred = curr_predictor->predict(ip, target);
        curr_predictor->update(pred, taken, ip, target);
    }
}

VOID Instruction(INS ins, void * v)
{
    if (INS_Category(ins) == XED_CATEGORY_COND_BR)
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)cond_branch_instruction,
                       IARG_INST_PTR, IARG_BRANCH_TARGET_ADDR, IARG_BRANCH_TAKEN,
                       IARG_END);
    else if (INS_IsCall(ins))
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)call_instruction,
                       IARG_INST_PTR, IARG_BRANCH_TARGET_ADDR,
                       IARG_UINT32, INS_Size(ins), IARG_END);
    else if (INS_IsRet(ins))
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)ret_instruction,
                       IARG_INST_PTR, IARG_BRANCH_TARGET_ADDR, IARG_END);

    // For BTB we instrument all branches except returns
    if (INS_IsBranch(ins) && !INS_IsRet(ins))
    INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)branch_instruction,
                   IARG_INST_PTR, IARG_BRANCH_TARGET_ADDR, IARG_BRANCH_TAKEN,
                   IARG_END);

    // Count each and every instruction
    INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)count_instruction, IARG_END);
}

/* ===================================================================== */

VOID Fini(int code, VOID * v)
{
    bp_iterator_t bp_it;
    btb_iterator_t btb_it;
    ras_vec_iterator_t ras_it;

    // Report total instructions and total cycles
    outFile << "Total Instructions: " << total_instructions << "\n";
    outFile << "\n";

    outFile <<"RAS: (Correct - Incorrect)\n";
    for (ras_it = ras_vec.begin(); ras_it != ras_vec.end(); ++ras_it) {
        RAS *ras = *ras_it;
        outFile << ras->getNameAndStats() << "\n";
    }
    outFile << "\n";

    outFile <<"Branch Predictors: (Name - Correct - Incorrect)\n";
    for (bp_it = branch_predictors.begin(); bp_it != branch_predictors.end(); ++bp_it) {
        BranchPredictor *curr_predictor = *bp_it;
        outFile << "  " << curr_predictor->getName() << ": "
                << curr_predictor->getNumCorrectPredictions() << " "
                << curr_predictor->getNumIncorrectPredictions() << "\n";
    }
    outFile << "\n";

    outFile <<"BTB Predictors: (Name - Correct - Incorrect - TargetCorrect)\n";
    for (btb_it = btb_predictors.begin(); btb_it != btb_predictors.end(); ++btb_it) {
        BTBPredictor *curr_predictor = *btb_it;
        outFile << "  " << curr_predictor->getName() << ": "
                << curr_predictor->getNumCorrectPredictions() << " "
                << curr_predictor->getNumIncorrectPredictions() << " "
                << curr_predictor->getNumCorrectTargetPredictions() << "\n";
    }

    outFile.close();
}

/* ===================================================================== */

VOID InitPredictors()
{
    // Static predictors
    branch_predictors.push_back(new AlwaysTakenPredictor());
    // branch_predictors.push_back(new BTFNTPredictor());

    // Best predictor from 5.3(iii)
    // Αν τελικά διάλεξες άλλο FSM, άλλαξε μόνο αυτό το ένα line
    // branch_predictors.push_back(new FSM2BitPredictor(14, "ABACBDCD", 3, "Best-2bit-FSM"));

    // Pentium-M predictor
    // branch_predictors.push_back(new PentiumMBranchPredictor());

    // Local-history predictors
    // PHT fixed = 8192 entries x 2 bits = 16384 bits
    // Remaining BHT budget = 16384 bits
    // X=2048 => Z=8
    // X=4096 => Z=4
    // X=8192 => Z=2
    // branch_predictors.push_back(new LocalHistoryPredictor(11, 8)); // 2048 entries
    // branch_predictors.push_back(new LocalHistoryPredictor(12, 4)); // 4096 entries
    // branch_predictors.push_back(new LocalHistoryPredictor(13, 2)); // 8192 entries

    // Global-history predictors
    // Z chosen so that PHT overhead = 32K bits with 2-bit counters => 16384 entries
    // branch_predictors.push_back(new GlobalHistoryPredictor(4, 14));
    // branch_predictors.push_back(new GlobalHistoryPredictor(8, 14));
    // branch_predictors.push_back(new GlobalHistoryPredictor(12, 14));

    // Perceptrons with ~32K-bit overhead
    // weight bits = 1 + floor(log2(theta))
    // around-32K choices
    // branch_predictors.push_back(new PerceptronPredictor(256, 20)); // ~32256 bits
    branch_predictors.push_back(new PerceptronPredictor(128, 32)); // ~29568 bits
    branch_predictors.push_back(new PerceptronPredictor(64, 60));  // ~31232 bits

    // Alpha 21264
    // branch_predictors.push_back(new Alpha21264Predictor());

    // Tournament predictors
    // branch_predictors.push_back(
    //     new TournamentPredictor(
    //         new NbitPredictor(13, 2),                // 16K bits
    //         new GlobalHistoryPredictor(8, 13),      // 8192 entries => 16K bits
    //         10,
    //         "Tournament-2bit-vs-Global"
    //     )
    // );

    // branch_predictors.push_back(
    //     new TournamentPredictor(
    //         new NbitPredictor(13, 2),                // 16K bits
    //         new FSM2BitPredictor(13, "ABADADCD", 3, "FSM16K"),
    //         10,
    //         "Tournament-2bit-vs-FSM"
    //     )
    // );

    branch_predictors.push_back(
        new TournamentPredictor(
            new NbitPredictor(13, 2),                // 16K bits
            new PerceptronPredictor(32, 60),         // ~15616 bits
            10,
            "Tournament-2bit-vs-Perceptron"
        )
    );

    // branch_predictors.push_back(
    //     new TournamentPredictor(
    //         new GlobalHistoryPredictor(12, 13),      // 16K bits
    //         new PerceptronPredictor(32, 60),         // ~15616 bits
    //         11,
    //         "Tournament-Global-vs-Perceptron"
    //     )
    // );
}


VOID InitRas()
{
    // for (UINT32 i = 4; i <= 32; i*=2)
    //     ras_vec.push_back(new RAS(i));
}

int main(int argc, char *argv[])
{
    PIN_InitSymbols();

    if(PIN_Init(argc,argv))
        return Usage();

    // Open output file
    outFile.open(KnobOutputFile.Value().c_str());

    // Initialize predictors and RAS vector
    InitPredictors();
    InitRas();

    // Instrument function calls in order to catch __parsec_roi_{begin,end}
    INS_AddInstrumentFunction(Instruction, 0);

    // Called when the instrumented application finishes its execution
    PIN_AddFiniFunction(Fini, 0);

    // Never returns
    PIN_StartProgram();
    
    return 0;
}

/* ===================================================================== */
/* eof */
/* ===================================================================== */
