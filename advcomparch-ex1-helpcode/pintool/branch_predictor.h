#ifndef BRANCH_PREDICTOR_H
#define BRANCH_PREDICTOR_H

#include <sstream> // std::ostringstream
#include <cmath>   // pow()
#include <cstring> // memset()

/**
 * A generic BranchPredictor base class.
 * All predictors can be subclasses with overloaded predict() and update()
 * methods.
 **/
class BranchPredictor
{
public:
    BranchPredictor() : correct_predictions(0), incorrect_predictions(0) {};
    virtual ~BranchPredictor() {};

    virtual bool predict(ADDRINT ip, ADDRINT target) = 0;
    virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) = 0;
    virtual string getName() = 0;

    UINT64 getNumCorrectPredictions() { return correct_predictions; }
    UINT64 getNumIncorrectPredictions() { return incorrect_predictions; }

    void resetCounters() { correct_predictions = incorrect_predictions = 0; };

protected:
    void updateCounters(bool predicted, bool actual) {
        if (predicted == actual)
            correct_predictions++;
        else
            incorrect_predictions++;
    };

private:
    UINT64 correct_predictions;
    UINT64 incorrect_predictions;
};

class NbitPredictor : public BranchPredictor
{
public:
    NbitPredictor(unsigned index_bits_, unsigned cntr_bits_)
        : BranchPredictor(), index_bits(index_bits_), cntr_bits(cntr_bits_) {
        table_entries = 1 << index_bits;
        TABLE = new unsigned long long[table_entries];
        memset(TABLE, 0, table_entries * sizeof(*TABLE));
        
        COUNTER_MAX = (1 << cntr_bits) - 1;
    };
    ~NbitPredictor() { delete TABLE; };

    virtual bool predict(ADDRINT ip, ADDRINT target) {
        unsigned int ip_table_index = ip % table_entries;
        unsigned long long ip_table_value = TABLE[ip_table_index];
        unsigned long long prediction = ip_table_value >> (cntr_bits - 1);
        return (prediction != 0);
    };

    virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) {
        unsigned int ip_table_index = ip % table_entries;
        if (actual) {
            if (TABLE[ip_table_index] < COUNTER_MAX)
                TABLE[ip_table_index]++;
        } else {
            if (TABLE[ip_table_index] > 0)
                TABLE[ip_table_index]--;
        }
        
        updateCounters(predicted, actual);
    };

    virtual string getName() {
        std::ostringstream stream;
        stream << "Nbit-" << pow(2.0,double(index_bits)) / 1024.0 << "K-" << cntr_bits;
        return stream.str();
    }

private:
    unsigned int index_bits, cntr_bits;
    unsigned int COUNTER_MAX;
    
    /* Make this unsigned long long so as to support big numbers of cntr_bits. */
    unsigned long long *TABLE;
    unsigned int table_entries;
};

// class SaturatingCounterPredictor : public BranchPredictor {
// 	public:
// 		SaturatingCounterPredictor(unsigned index_bits_): BranchPredictor(), index_bits(index_bits_){
// 			table_entries = 1 << index_bits;
// 			STATE = new int[table_entries];
// 			memset(STATE, 0, table_entries * sizeof(int));
// 		}

// 		~SaturatingCounterPredictor() {
// 			delete[] STATE;
// 		}

// 		virtual bool predict(ADDRINT ip, ADDRINT target) {
// 			unsigned int idx = ip % table_entries;
// 			return (STATE[idx] >= 2);
// 		}

// 		virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) {
// 			unsigned int idx = ip % table_entries;

// 			if (actual) {
// 				if (STATE[idx] < 3)
// 					STATE[idx]++;
// 			} else {
// 				if (STATE[idx] > 0)
// 					STATE[idx]--;
// 			}

// 			updateCounters(predicted, actual);
// 		}

// 		virtual string getName() {
// 			std::ostringstream stream;
// 			stream << "2bit-SaturatingCounter-" << (table_entries / 1024) << "K";
// 			return stream.str();
// 		}

// 	private:
// 		unsigned int index_bits;
// 		unsigned int table_entries;
// 		int* STATE;
// 	};



class FSM2BitPredictor : public BranchPredictor{
	public:
		FSM2BitPredictor(unsigned index_bits_,const std::string& transitions_,unsigned output_mask_,const std::string& name_)
		: BranchPredictor(),index_bits(index_bits_),transitions(transitions_),output_mask(output_mask_),name(name_){
			table_entries = 1 << index_bits;
			STATE = new unsigned char[table_entries];

			for (unsigned i = 0; i < table_entries; i++)
				STATE[i] = 0;   // αρχική κατάσταση A

			// transitions string: A0 A1 B0 B1 C0 C1 D0 D1
			for (int s = 0; s < 4; s++) {
				next_state[s][0] = charToState(transitions[2 * s]);
				next_state[s][1] = charToState(transitions[2 * s + 1]);
			}

			// output bits για A,B,C,D
			// π.χ. output_mask = 3 => binary 0011 => A=0, B=0, C=1, D=1
			for (int s = 0; s < 4; s++) {
				prediction_bit[s] = (output_mask >> (3 - s)) & 1;
			}
		}

		~FSM2BitPredictor() {
			delete[] STATE;
		}

		virtual bool predict(ADDRINT ip, ADDRINT target) {
			unsigned idx = ip % table_entries;
			unsigned state = STATE[idx];
			return prediction_bit[state];
		}

		virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) {
			unsigned idx = ip % table_entries;
			unsigned curr = STATE[idx];
			STATE[idx] = next_state[curr][actual ? 1 : 0];
			updateCounters(predicted, actual);
		}

		virtual string getName() {
			std::ostringstream stream;
			stream << name << " (" << transitions << ":" << output_mask << ")";
			return stream.str();
		}

	private:
		unsigned char charToState(char c) {
			if (c == 'A') return 0;
			if (c == 'B') return 1;
			if (c == 'C') return 2;
			return 3; // D
		}

		unsigned index_bits;
		unsigned table_entries;
		unsigned char* STATE;

		std::string transitions;
		unsigned output_mask;
		std::string name;

		unsigned char next_state[4][2];
		bool prediction_bit[4];
};

// Fill in the BTB implementation ...
class BTBPredictor : public BranchPredictor
{
public:
	BTBPredictor(int btb_lines, int btb_assoc)
	     : table_lines(btb_lines), table_assoc(btb_assoc)
	{
		/* ... fill me ... */
	}

	~BTBPredictor() {
		/* ... fill me ... */
	}

    virtual bool predict(ADDRINT ip, ADDRINT target) {
		/* ... fill me ... */
		return false;
	}

    virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) {
		/* ... fill me ... */
	}

    virtual string getName() { 
        std::ostringstream stream;
		stream << "BTB-" << table_lines << "-" << table_assoc;
		return stream.str();
	}

    UINT64 getNumCorrectTargetPredictions() { 
		/* ... fill me ... */
		return 0;
	}

private:
	int table_lines, table_assoc;
};


// Perceptron class
class PerceptronPredictor : public BranchPredictor
{
	// Perceptrons table size.
	int perceptronTableSize_ = 4096; 
	// History table capacity.
	int historyTableSize_ = 60;
	// The theta value used as the threshold. We use the value found optimal in the paper. (Go read the paper!)
	int kTheta_ = static_cast<int>(1.93 * historyTableSize_ + 14);
	// Start offset for history_.
	int history_start_ = 0;
	// Vector that holds history values
	std::vector<int> history_;
	// The bias, i.e., w_0 for each perceptron. Initialized to 1.
	std::vector<int> bias_;
	// The perceptrons table.
	std::vector<std::vector<int>> weights_;

	// Training the perceptron requires the last predictions output, y. Our update method only provides the prediction as a bool taken/not-taken. We save the last y here and use it on the immediate next 'update' call.
	int last_prediction_y = 0;
public:
	// Constructor
	PerceptronPredictor(int perceptronTableSize, int historyTableSize) : BranchPredictor(), perceptronTableSize_(perceptronTableSize), historyTableSize_(historyTableSize) {
        
	history_.resize(historyTableSize_, -1);
        bias_.resize(perceptronTableSize_, 1);
        weights_.resize(perceptronTableSize_, std::vector<int>(historyTableSize_, 0));
        history_start_ = 0;
        last_prediction_y = 0;
    } 

private:
	// Overriden "predict" method...
	// ---
	virtual bool predict(ADDRINT ip, ADDRINT target) {
		int computed_prediction = compute(ip % perceptronTableSize_);
		last_prediction_y = computed_prediction; // Save y to use inside update!
		//std::cout << "I saved: " << prediction << std::endl;
		if (computed_prediction >= 0){
			return true;
		}
		else {
			return false;
		}
  	}
	// ---
	
	
	// Overriden "getName" method...
	// ---
	virtual string getName(){
		std::string output = "Perceptron Branch Predictor (perceptrons: " + std::to_string(perceptronTableSize_) + ", history size: " + std::to_string(historyTableSize_);
		return output;
  	}
	// ---


	// Overriden "update" method...
	// ---
	virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) {
		int key = ip % perceptronTableSize_;
		int prediction = last_prediction_y; // Use the saved value y from last prediction 
		int br_taken = 0;
	
		if (actual == true) {
			br_taken = 1;
		}
		else {
			br_taken = -1;
		}
		updateCounters(predicted, actual);
		train(key, prediction, br_taken);
	}
	// ---

	int sign(int val) {
  		return (val >= 0) ? 1 : -1;
	}
  
	// Computes the y value of the perceptron with the given key.
	int compute(int key) {
		int y = bias_[key];
		for (int i = 0; i < historyTableSize_; ++i) {
			int h = ((history_start_ - 1) -i + historyTableSize_) % historyTableSize_;
			y += weights_[key][i] * history_[h];
		}
		return y;
  	}

  	// Trains the perceptron. Takes as inputs:
  	// - key: branch address hashed with table size,
  	// - y: the output y of the last prediction,
  	// - t: the actual result of last prediction (taken/not-taken). This must be 1 for 'taken' and -1 for 'not taken' .
  	void train(int key, int y, int t) {
		// Only train the perceptron if we were wrong or if we didn't give a strong enough response.
		if (sign(y) != t || abs(y) <= kTheta_) {
		  	int b = bias_[key] + t;
		  	bias_[key] = b;
			
			for (int i = 0; i < historyTableSize_; ++i) {
				int h = ((history_start_ - 1) - i + historyTableSize_) % historyTableSize_;
				int xi = history_[h];
	
				if (t == xi)
					weights_[key][i] += 1;
				else
					weights_[key][i] -= 1;
			}
		}
	
		history_[history_start_] = t;
		history_start_ = (1 + history_start_) % historyTableSize_;
	  }
};

class AlwaysTakenPredictor : public BranchPredictor
{
public:
    AlwaysTakenPredictor() : BranchPredictor() {}

    virtual bool predict(ADDRINT ip, ADDRINT target) {
        return true;
    }

    virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) {
        updateCounters(predicted, actual);
    }

    virtual string getName() {
        return "Static-AlwaysTaken";
    }
};

class BTFNTPredictor : public BranchPredictor
{
public:
    BTFNTPredictor() : BranchPredictor() {}

    virtual bool predict(ADDRINT ip, ADDRINT target) {
        return (target < ip);
    }

    virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) {
        updateCounters(predicted, actual);
    }

    virtual string getName() {
        return "Static-BTFNT";
    }
};

class GlobalHistoryPredictor : public BranchPredictor
{
public:
    GlobalHistoryPredictor(unsigned history_bits_, unsigned pht_index_bits_)
        : BranchPredictor(),
          history_bits(history_bits_),
          pht_index_bits(pht_index_bits_),
          ghr(0)
    {
        pht_entries = 1 << pht_index_bits;
        PHT = new unsigned char[pht_entries];
        memset(PHT, 0, pht_entries * sizeof(*PHT));
    }

    ~GlobalHistoryPredictor() {
        delete[] PHT;
    }

    virtual bool predict(ADDRINT ip, ADDRINT target) {
        unsigned idx = ghr % pht_entries;
        return (PHT[idx] >= 2);
    }

    virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) {
        unsigned idx = ghr % pht_entries;

        if (actual) {
            if (PHT[idx] < 3) PHT[idx]++;
        } else {
            if (PHT[idx] > 0) PHT[idx]--;
        }

        ghr = ((ghr << 1) | (actual ? 1 : 0)) & ((1u << history_bits) - 1);
        updateCounters(predicted, actual);
    }

    virtual string getName() {
        std::ostringstream stream;
        stream << "GlobalHistory-H" << history_bits << "-PHT" << pht_entries;
        return stream.str();
    }

private:
    unsigned history_bits;
    unsigned pht_index_bits;
    unsigned pht_entries;
    unsigned ghr;
    unsigned char* PHT;
};

class LocalHistoryPredictor : public BranchPredictor
{
public:
    LocalHistoryPredictor(unsigned bht_index_bits_, unsigned local_history_bits_)
        : BranchPredictor(),
          bht_index_bits(bht_index_bits_),
          local_history_bits(local_history_bits_)
    {
        bht_entries = 1 << bht_index_bits;
        pht_entries = 8192;

        BHT = new unsigned[bht_entries];
        PHT = new unsigned char[pht_entries];

        memset(BHT, 0, bht_entries * sizeof(*BHT));
        memset(PHT, 0, pht_entries * sizeof(*PHT));
    }

    ~LocalHistoryPredictor() {
        delete[] BHT;
        delete[] PHT;
    }

    virtual bool predict(ADDRINT ip, ADDRINT target) {
        unsigned bht_idx = ip % bht_entries;
        unsigned local_hist = BHT[bht_idx];
        unsigned pht_idx = local_hist % pht_entries;
        return (PHT[pht_idx] >= 2);
    }

    virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) {
        unsigned bht_idx = ip % bht_entries;
        unsigned local_hist = BHT[bht_idx];
        unsigned pht_idx = local_hist % pht_entries;

        if (actual) {
            if (PHT[pht_idx] < 3) PHT[pht_idx]++;
        } else {
            if (PHT[pht_idx] > 0) PHT[pht_idx]--;
        }

        BHT[bht_idx] = ((local_hist << 1) | (actual ? 1 : 0)) & ((1u << local_history_bits) - 1);
        updateCounters(predicted, actual);
    }

    virtual string getName() {
        std::ostringstream stream;
        stream << "LocalHistory-BHT" << bht_entries << "-H" << local_history_bits;
        return stream.str();
    }

private:
    unsigned bht_index_bits;
    unsigned local_history_bits;
    unsigned bht_entries;
    unsigned pht_entries;

    unsigned* BHT;
    unsigned char* PHT;
};

class Alpha21264Predictor : public BranchPredictor
{
public:
    Alpha21264Predictor()
        : BranchPredictor(), ghr(0)
    {
        local_history_entries = 1024;
        local_pht_entries = 1024;
        global_pht_entries = 4096;
        choice_entries = 4096;

        localHistoryTable = new unsigned[local_history_entries];
        localPHT = new unsigned char[local_pht_entries];
        globalPHT = new unsigned char[global_pht_entries];
        choicePHT = new unsigned char[choice_entries];

        memset(localHistoryTable, 0, local_history_entries * sizeof(*localHistoryTable));
        memset(localPHT, 0, local_pht_entries * sizeof(*localPHT));
        memset(globalPHT, 0, global_pht_entries * sizeof(*globalPHT));
        memset(choicePHT, 0, choice_entries * sizeof(*choicePHT));
    }

    ~Alpha21264Predictor() {
        delete[] localHistoryTable;
        delete[] localPHT;
        delete[] globalPHT;
        delete[] choicePHT;
    }

    virtual bool predict(ADDRINT ip, ADDRINT target) {
        unsigned local_idx = ip % local_history_entries;
        unsigned local_hist = localHistoryTable[local_idx] & ((1u << 10) - 1);
        unsigned local_pred_idx = local_hist % local_pht_entries;
        unsigned global_idx = ghr % global_pht_entries;
        unsigned choice_idx = ghr % choice_entries;

        last_local_prediction = (localPHT[local_pred_idx] >= 4);  // 3-bit counter
        last_global_prediction = (globalPHT[global_idx] >= 2);    // 2-bit counter

        if (choicePHT[choice_idx] >= 2)
            return last_global_prediction;
        else
            return last_local_prediction;
    }

    virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) {
        unsigned local_idx = ip % local_history_entries;
        unsigned local_hist = localHistoryTable[local_idx] & ((1u << 10) - 1);
        unsigned local_pred_idx = local_hist % local_pht_entries;
        unsigned global_idx = ghr % global_pht_entries;
        unsigned choice_idx = ghr % choice_entries;

        // update local predictor (3-bit saturating counter)
        if (actual) {
            if (localPHT[local_pred_idx] < 7) localPHT[local_pred_idx]++;
            if (globalPHT[global_idx] < 3) globalPHT[global_idx]++;
        } else {
            if (localPHT[local_pred_idx] > 0) localPHT[local_pred_idx]--;
            if (globalPHT[global_idx] > 0) globalPHT[global_idx]--;
        }

        bool local_correct = (last_local_prediction == actual);
        bool global_correct = (last_global_prediction == actual);

        if (local_correct && !global_correct) {
            if (choicePHT[choice_idx] > 0) choicePHT[choice_idx]--;
        } else if (!local_correct && global_correct) {
            if (choicePHT[choice_idx] < 3) choicePHT[choice_idx]++;
        }

        localHistoryTable[local_idx] =
            ((localHistoryTable[local_idx] << 1) | (actual ? 1 : 0)) & ((1u << 10) - 1);
        ghr = ((ghr << 1) | (actual ? 1 : 0)) & ((1u << 12) - 1);

        updateCounters(predicted, actual);
    }

    virtual string getName() {
        return "Alpha21264";
    }

private:
    unsigned* localHistoryTable;
    unsigned char* localPHT;
    unsigned char* globalPHT;
    unsigned char* choicePHT;

    unsigned local_history_entries;
    unsigned local_pht_entries;
    unsigned global_pht_entries;
    unsigned choice_entries;

    unsigned ghr;
    bool last_local_prediction;
    bool last_global_prediction;
};

class TournamentPredictor : public BranchPredictor
{
public:
    TournamentPredictor(BranchPredictor* p0_, BranchPredictor* p1_, unsigned meta_index_bits_, const std::string& name_)
        : BranchPredictor(), p0(p0_), p1(p1_), name(name_)
    {
        meta_entries = 1 << meta_index_bits_;
        META = new unsigned char[meta_entries];
        memset(META, 0, meta_entries * sizeof(*META));
        last_p0 = false;
        last_p1 = false;
    }

    ~TournamentPredictor() {
        delete[] META;
        delete p0;
        delete p1;
    }

    virtual bool predict(ADDRINT ip, ADDRINT target) {
        last_p0 = p0->predict(ip, target);
        last_p1 = p1->predict(ip, target);

        unsigned idx = ip % meta_entries;
        return (META[idx] >= 2) ? last_p1 : last_p0;
    }

    virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) {
        p0->update(last_p0, actual, ip, target);
        p1->update(last_p1, actual, ip, target);

        unsigned idx = ip % meta_entries;
        bool p0_correct = (last_p0 == actual);
        bool p1_correct = (last_p1 == actual);

        if (p0_correct && !p1_correct) {
            if (META[idx] > 0) META[idx]--;
        } else if (!p0_correct && p1_correct) {
            if (META[idx] < 3) META[idx]++;
        }

        updateCounters(predicted, actual);
    }

    virtual string getName() {
        return name;
    }

private:
    BranchPredictor* p0;
    BranchPredictor* p1;
    std::string name;

    unsigned meta_entries;
    unsigned char* META;

    bool last_p0;
    bool last_p1;
};


#endif
