
#include <iostream>
#include <sstream>
#include <cstring>
#include <iomanip>
#include <cassert>
#include <algorithm>

#include "Errors.h"
#include "NutScript.h"
#include "Formatters.h"
#include "Expressions.h"
#include "Statements.h"
#include "BlockState.h"


enum Opcode
{
	OP_LINE = 0,
	OP_LOAD,
	OP_LOADINT,
	OP_LOADFLOAT,
	OP_DLOAD,
	OP_TAILCALL,
	OP_CALL,
	OP_PREPCALL,
	OP_PREPCALLK,
	OP_GETK,
	OP_MOVE,
	OP_NEWSLOT,
	OP_DELETE,
	OP_SET,
	OP_GET,
	OP_EQ,
	OP_NE,
	OP_ARITH,
	OP_BITW,
	OP_RETURN,
	OP_LOADNULLS,
	OP_LOADROOTTABLE,
	OP_LOADBOOL,
	OP_DMOVE,
	OP_JMP,
	OP_JNZ,
	OP_JZ,
	OP_LOADFREEVAR,
	OP_VARGC,
	OP_GETVARGV,
	OP_NEWTABLE,
	OP_NEWARRAY,
	OP_APPENDARRAY,
	OP_GETPARENT,
	OP_COMPARITH,
	OP_COMPARITHL,
	OP_INC,
	OP_INCL,
	OP_PINC,
	OP_PINCL,
	OP_CMP,
	OP_EXISTS,
	OP_INSTANCEOF,
	OP_AND,
	OP_OR,
	OP_NEG,
	OP_NOT,
	OP_BWNOT,
	OP_CLOSURE,
	OP_YIELD,
	OP_RESUME,
	OP_FOREACH,
	OP_POSTFOREACH,
	OP_DELEGATE,
	OP_CLONE,
	OP_TYPEOF,
	OP_PUSHTRAP,
	OP_POPTRAP,
	OP_THROW,
	OP_CLASS,
	OP_NEWSLOTA
};

enum BitWiseOpcode 
{
	BW_AND = 0,
	BW_OR = 2,	
	BW_XOR = 3,
	BW_SHIFTL = 4,
	BW_SHIFTR = 5,
	BW_USHIFTR = 6
};

enum ComparisionOpcode 
{
	CMP_G = 0,
	CMP_GE = 2,	
	CMP_L = 3,
	CMP_LE = 4
};

const char* OpcodeNames[] = 
{
	"OP_LINE",
	"OP_LOAD",
	"OP_LOADINT",
	"OP_LOADFLOAT",
	"OP_DLOAD",
	"OP_TAILCALL",
	"OP_CALL",
	"OP_PREPCALL",
	"OP_PREPCALLK",
	"OP_GETK",
	"OP_MOVE",
	"OP_NEWSLOT",
	"OP_DELETE",
	"OP_SET",
	"OP_GET",
	"OP_EQ",
	"OP_NE",
	"OP_ARITH",
	"OP_BITW",
	"OP_RETURN",
	"OP_LOADNULLS",
	"OP_LOADROOTTABLE",
	"OP_LOADBOOL",
	"OP_DMOVE",
	"OP_JMP",
	"OP_JNZ",
	"OP_JZ",
	"OP_LOADFREEVAR",
	"OP_VARGC",
	"OP_GETVARGV",
	"OP_NEWTABLE",
	"OP_NEWARRAY",
	"OP_APPENDARRAY",
	"OP_GETPARENT",
	"OP_COMPARITH",
	"OP_COMPARITHL",
	"OP_INC",
	"OP_INCL",
	"OP_PINC",
	"OP_PINCL",
	"OP_CMP",
	"OP_EXISTS",
	"OP_INSTANCEOF",
	"OP_AND",
	"OP_OR",
	"OP_NEG",
	"OP_NOT",
	"OP_BWNOT",
	"OP_CLOSURE",
	"OP_YIELD",
	"OP_RESUME",
	"OP_FOREACH",
	"OP_POSTFOREACH",
	"OP_DELEGATE",
	"OP_CLONE",
	"OP_TYPEOF",
	"OP_PUSHTRAP",
	"OP_POPTRAP",
	"OP_THROW",
	"OP_CLASS",
	"OP_NEWSLOTA"
};

const int BitWiseOpcodeNames[] =
{
	'&',
	0x3f3f,//'??',
	'|',
	'^',
	0x3c3c,//'<<',
	0x3e3e,//'>>',
	0x3c3c,//'<<'
};

const int ComparisionOpcodeNames[] = 
{
	'>',
	0x3f3f,//'??',
	0x3e3d,//'>=',
	'<',
	0x3c3d//'<='
};


static const unsigned int OpcodesCount = sizeof(OpcodeNames) / sizeof(OpcodeNames[0]);


// ***************************************************************************************************************
ExpressionPtr ToTemporaryVariable( ExpressionPtr exp )
{
	if (exp->GetType() == Exp_LocalVariable)
		return ExpressionPtr(new VariableExpression( static_pointer_cast<LocalVariableExpression>(exp)->GetVariableName() ));
	else
		return exp;
}


// ***************************************************************************************************************
class VMState
{
public:
	struct StackElement
	{
		ExpressionPtr expression;
		std::vector<StatementPtr> pendingStatements;
	};

	typedef shared_ptr< std::vector<StackElement> > StackCopyPtr;

private:
	const NutFunction& m_Parent;

	BlockStatementPtr m_Block;
	std::vector<StackElement> m_Stack;
	std::vector<int> m_JNZInstructions;
	int m_IP;

public:
	BlockState m_BlockState;

	VMState( const NutFunction& parent, int64_t stackSize )
	: m_Parent(parent)
	{
		m_Stack.resize((size_t) stackSize);
		m_IP = 0;
		m_Block = BlockStatementPtr(new BlockStatement);
		m_BlockState.blockStart = -1;
		m_BlockState.blockEnd = parent.m_Instructions.size() + 2;

		// Find all JNZ instructions in code with beck jump - this will be oure do..while loops
		for( int i = 0; i < (int)parent.m_Instructions.size(); ++i)
			if (parent.m_Instructions[i].op == OP_JNZ && parent.m_Instructions[i].arg1 < 0)
				m_JNZInstructions.push_back(i);
	}

	int PopJNZInstructionWithTarget( int address )
	{
		// Find last JNZ instruction that points at specified address (we need last to find
		// outermost do..while block)

		for( int i = (int)m_JNZInstructions.size() - 1; i >= 0; --i)
			if ((m_JNZInstructions[i] + 1 + m_Parent.m_Instructions[m_JNZInstructions[i]].arg1) == address)
			{
				int pos = m_JNZInstructions[i];
				m_JNZInstructions.erase(m_JNZInstructions.begin() + i);
				return pos;
			}

		return -1;
	}

	void NextInstruction( void )
	{
		// Search for local variables that expires at previously finished instruction
		for( vector<NutFunction::LocalVarInfo>::const_iterator i = m_Parent.m_Locals.begin(); i != m_Parent.m_Locals.end(); ++i)
		{		
			if (i->end_op == (m_IP - 1))
			{
				m_Stack[(size_t) i->pos].expression = ExpressionPtr();
				m_Stack[(size_t) i->pos].pendingStatements.clear();
			}
		}

		// Move to next instruction
		m_IP += 1;
	}

	bool EndOfInstructions( void ) const
	{
		return m_IP >= (int)m_Parent.m_Instructions.size();
	}

	BlockStatementPtr PushBlock( void )
	{
		BlockStatementPtr prevBlock = m_Block;
		m_Block = BlockStatementPtr(new BlockStatement);

		return prevBlock;
	}

	BlockStatementPtr PopBlock( BlockStatementPtr block )
	{
		BlockStatementPtr prevBlock = m_Block;
		m_Block = block;

		return prevBlock;
	}

	void PushStatement( StatementPtr statement )
	{
		m_Block->Add(statement);
	}

	void ClearPendingStatement( StatementPtr stat, ExpressionPtr usedExpression )
	{
		if (stat->GetType() == Stat_Expression)
		{
			ExpressionStatementPtr pendingStatement = static_pointer_cast<ExpressionStatement>(stat);

			if (pendingStatement->Equals(usedExpression))
			{
					pendingStatement->Clear();
			}
			else if (usedExpression->GetType() == Exp_Operator && static_pointer_cast<OperatorExpression>(usedExpression)->GetOperatorType() == '?:')
			{
				shared_ptr<ConditionOperatorExpression> conditionExp = static_pointer_cast<ConditionOperatorExpression>(usedExpression);
				if (pendingStatement->Equals(conditionExp->GetConditionExp()) ||
					pendingStatement->Equals(conditionExp->GetTrueExp()) ||
					pendingStatement->Equals(conditionExp->GetFalseExp()))
				{
					pendingStatement->Clear();
				}
			}
		}
		else if (stat->GetType() == Stat_If)
		{
			shared_ptr<IfStatement> ifStatement = static_pointer_cast<IfStatement>(stat);
				ifStatement->Cancel();
		}
	}

	ExpressionPtr GetVar( int pos )
	{
		if (pos < 0 || pos >= (int)m_Stack.size())
			throw Error("Accessing non valid stack variable.");

		if (!m_Stack[pos].expression)
		{
			// Stack variable is not initialized - temporary make marker for it
			std::ostringstream marker;
			marker << "$[stack offset " << pos << "]";

			return ExpressionPtr(new VariableExpression(marker.str()));
		}
		else if (!m_Stack[pos].pendingStatements.empty())
		{
			// Pending expressions deletion
			for( vector<StatementPtr>::iterator i = m_Stack[pos].pendingStatements.begin(); i != m_Stack[pos].pendingStatements.end(); ++i)
				ClearPendingStatement(*i, m_Stack[pos].expression);

			m_Stack[pos].pendingStatements.clear();
		}
			
		return m_Stack[pos].expression;
	}

	bool InitVar( int pos, ExpressionPtr exp = ExpressionPtr(), bool foreachInit = false )
	{
		if (pos < 0 || pos >= (int)m_Stack.size())
			throw Error("Accessing non valid stack position.");

		if (exp && exp->GetType() == Exp_Null)
			exp = ExpressionPtr();

		// Check for local initialization
		for( vector<NutFunction::LocalVarInfo>::const_iterator i = m_Parent.m_Locals.begin(); i != m_Parent.m_Locals.end(); ++i)
		{
			// Variable stack address
			if (i->pos != pos) continue;

			// Match foreach state variables
			if (i->foreachLoopState != foreachInit) continue;

			// Variable scope range
			if (m_IP != i->start_op && (!foreachInit || m_IP < i->start_op || m_IP > i->end_op)) continue;

			if (m_Stack[pos].expression && m_Stack[pos].expression->GetType() == Exp_LocalVariable 
				&& static_pointer_cast<LocalVariableExpression>(m_Stack[pos].expression)->GetVariableName() == i->name)
			{
				// This variable is already initialized
				break;
			}

			if (i->end_op > m_BlockState.blockEnd && m_BlockState.inLoop == 0 && m_BlockState.inSwitch == 0)
			{
				// Initialization of variable that reaches out of current if block - ignore
				continue;
			}

			// This is local initialization
			if (!foreachInit)
			{
				PushStatement(StatementPtr(new LocalVarInitStatement(i->name, pos, i->start_op, i->end_op, exp)));
			}

			m_Stack[pos].expression = ExpressionPtr(new LocalVariableExpression(i->name));
			m_Stack[pos].pendingStatements.clear();

			return true;
		}

		return false;
	}

	void SetVar( int pos, ExpressionPtr exp, bool expIsStatementLike = false )
	{
		if (pos < 0 || pos >= (int)m_Stack.size())
			throw Error("Accessing non valid stack position.");

		if (InitVar(pos, exp))
			return;

		if (exp->IsOperator())
			expIsStatementLike = true;

		if (m_Stack[pos].expression && m_Stack[pos].expression->GetType() == Exp_LocalVariable)
		{
			// Setting value to local variable - generate statement for this
			ExpressionPtr assignExp = ExpressionPtr(new BinaryOperatorExpression('=', m_Stack[pos].expression, exp));
			PushStatement(StatementPtr(new ExpressionStatement(assignExp)));
		}
		else
		{
			// Setting to intermediate variable
			if (expIsStatementLike)
			{
				// but expression itself may be used as statement - we must put it in pending state
				// and assure that it will be invoked only once, when not by usage of temporary
				// stack register that by explicit statement
				ExpressionStatementPtr statement = ExpressionStatementPtr(new ExpressionStatement(exp));
				PushStatement(statement);

				m_Stack[pos].pendingStatements.push_back(statement);
			}
			else
			{
				m_Stack[pos].pendingStatements.clear();
			}

			m_Stack[pos].expression = ToTemporaryVariable(exp);
		}
	}


	ExpressionPtr& AtStack( int64_t pos )
	{
		if (pos < 0 || pos >= m_Stack.size())
			throw Error("Accessing non valid stack position.");

		return m_Stack[(size_t) pos].expression;
	}

	StackCopyPtr CloneStack( void ) const
	{
		return StackCopyPtr(new std::vector<StackElement>(m_Stack.begin(), m_Stack.end()));
	}

	void SwapStacks( StackCopyPtr copy )
	{
		m_Stack.swap(*copy);
	}

	void MergeStackVariable( ExpressionPtr branchCondition_TrueToUseCopy, int pos, StackElement& element, StatementPtr AdditionalPedningStatement )
	{
		if (m_Stack[pos].expression != element.expression && element.expression)
		{
			// Found difference in cloned stack
			if (!m_Stack[pos].expression)
			{
				m_Stack[pos].expression.swap(element.expression);
				m_Stack[pos].pendingStatements.swap(element.pendingStatements);
			}
			else
			{
				// Found two different expressions in stack and its copy - create condition expression out of both
				ExpressionPtr mergedVar = ExpressionPtr(
					new ConditionOperatorExpression(branchCondition_TrueToUseCopy, element.expression, m_Stack[pos].expression)
				);

				// Prepare merged pending expressions list
				std::vector<StatementPtr> pendingStatements(m_Stack[pos].pendingStatements.begin(), m_Stack[pos].pendingStatements.end());
				pendingStatements.insert(pendingStatements.end(), element.pendingStatements.begin(), element.pendingStatements.end());
				if (AdditionalPedningStatement)
					pendingStatements.push_back(AdditionalPedningStatement);

				if (InitVar(pos, mergedVar))
				{
					for( vector<StatementPtr>::iterator i = pendingStatements.begin(); i != pendingStatements.end(); ++i)
						ClearPendingStatement(*i, mergedVar);
				}
				else
				{
					m_Stack[pos].expression = mergedVar;
					m_Stack[pos].pendingStatements.swap(pendingStatements);
				}

				element.expression = ExpressionPtr();
				element.pendingStatements.clear();
			}
		}
	}

	void PrintOutput( std::ostream& out, int n )
	{
		m_Block->Postprocess();
		m_Block->GenerateBlockContentCode(out, n);
	}

	int IP( void ) const
	{
		return m_IP;
	}

	const NutFunction& Parent( void ) const
	{
		return m_Parent;
	}

	void PushUnknownOpcode( void )
	{
		std::ostringstream text;
		m_Parent.PrintOpcode(text, IP() - 1, m_Parent.m_Instructions[IP() - 1]);
		PushStatement(StatementPtr(new CommentStatement(text.str())));
	}
};



// ***************************************************************************************************************
// ***************************************************************************************************************
class FunctionGeneratingExpression : public FunctionExpression
{
private:
	const NutFunction& m_Function;
	std::vector<ExpressionPtr> m_Defaults;

public:
	explicit FunctionGeneratingExpression( int functionIndex, const NutFunction& function )
	: FunctionExpression(functionIndex)
	, m_Function(function)
	{
	}

	void AddDefault( ExpressionPtr value )
	{
		m_Defaults.push_back(value);
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		if (g_DebugMode)
		{
			out << "$[function #" << m_FunctionIndex << "]";
			return;
		}
		
		std::vector< std::string > defaults;
		for( vector<ExpressionPtr>::const_iterator i = m_Defaults.begin(); i != m_Defaults.end(); ++i)
		{
			std::ostringstream defaultBuffer;
			(*i)->GenerateCode(defaultBuffer, n + 1);
			defaults.push_back(defaultBuffer.str());
		}

		m_Function.GenerateFunctionSource(n, out, m_name, defaults);
	}
};



// ***************************************************************************************************************
// ***************************************************************************************************************
void NutFunction::DecompileStatement( VMState& state ) const
{
	int jnz = state.PopJNZInstructionWithTarget(state.IP());
	if (jnz > -1)
	{
		// Found start of do...while loop
		DecompileDoWhileLoop(state, jnz);
		return;
	}

	const Instruction& op = m_Instructions[state.IP()];
	int code = op.op;
	int arg0 = static_cast<unsigned char>(op.arg0);
	int arg1 = op.arg1;
	int arg2 = static_cast<unsigned char>(op.arg2);
	int arg3 = static_cast<unsigned char>(op.arg3);

	state.NextInstruction();
	
	switch(code)
	{
		case OP_LOAD:
			state.SetVar(arg0, ExpressionPtr(new ConstantExpression(m_Literals[arg1])));
			break;

		case OP_LOADINT:
			state.SetVar(arg0, ExpressionPtr(new ConstantExpression(static_cast<unsigned int>(arg1))));
			break;

		case OP_LOADFLOAT:
			state.SetVar(arg0, ExpressionPtr(new ConstantExpression( *((float*)&arg1) )));
			break;

		case OP_DLOAD:
			state.SetVar(arg0, ExpressionPtr(new ConstantExpression(m_Literals[arg1])));
			state.SetVar(arg2, ExpressionPtr(new ConstantExpression(m_Literals[arg3])));
			break;

		case OP_TAILCALL:
		case OP_CALL:
			{
				shared_ptr<FunctionCallExpression> exp = shared_ptr<FunctionCallExpression>(new FunctionCallExpression(state.GetVar(arg1)));
				for(int i = 1; i < arg3; ++i)
					exp->AddArgument(state.GetVar(arg2 + i));

				state.SetVar(arg0, exp, true);
			}
			break;

		case OP_PREPCALL:
		case OP_PREPCALLK:
			{
				ExpressionPtr key, obj;

				if (code == OP_PREPCALLK)
					key = ExpressionPtr(new ConstantExpression(m_Literals[arg1]));
				else
					key = state.GetVar(arg1);

				obj = state.GetVar(arg2);

				ExpressionPtr objAccess = ExpressionPtr(new ArrayIndexingExpression(obj, key));

				state.AtStack(arg3) = ExpressionPtr();
				state.AtStack(arg0) = objAccess;
			}
			break;

		case OP_GETK:
			state.SetVar(arg0, ExpressionPtr(new ArrayIndexingExpression(state.GetVar(arg2), ExpressionPtr(new ConstantExpression(m_Literals[arg1])))));
			break;

		case OP_MOVE:
			state.SetVar(arg0,  state.GetVar(arg1));
			break;

		// *** OP_NEWSLOT moved down

		case OP_DELETE:
			{
				ExpressionPtr derefExpr = ExpressionPtr(new ArrayIndexingExpression(state.GetVar(arg1), state.GetVar(arg2)));
				ExpressionPtr deleteExpt = ExpressionPtr(new UnaryOperatorExpression(OperatorExpression::OPER_DELETE, derefExpr));
				state.SetVar(arg0, deleteExpt, true);
			}
			break;


		case OP_SET:
			{
				ExpressionPtr leftArg = ExpressionPtr(new ArrayIndexingExpression(state.GetVar(arg1), state.GetVar(arg2)));
				ExpressionPtr assignExpr = ExpressionPtr(new BinaryOperatorExpression('=', leftArg, state.GetVar(arg3)));

				if (arg0 != arg3)
					state.SetVar(arg0, assignExpr, true);
				else
					state.PushStatement(StatementPtr(new ExpressionStatement(assignExpr)));
			}
			break;
		
		case OP_GET:
			state.SetVar(arg0, ExpressionPtr(new ArrayIndexingExpression(state.GetVar(arg1), state.GetVar(arg2))));
			break;

		case OP_EQ:
		case OP_NE:
			{
				ExpressionPtr right = (arg3 != 0) ? ExpressionPtr(new ConstantExpression(m_Literals[arg1])) : state.GetVar(arg1);
				ExpressionPtr op = ExpressionPtr(new BinaryOperatorExpression((code == OP_NE) ? '!=' : '==', state.GetVar(arg2), right));
				state.SetVar(arg0, op);
			}
			break;

		case OP_ARITH:
			state.SetVar(arg0, ExpressionPtr(new BinaryOperatorExpression(arg3, state.GetVar(arg2), state.GetVar(arg1))));
			break;

		case OP_BITW:
			state.SetVar(arg0, ExpressionPtr(new BinaryOperatorExpression(BitWiseOpcodeNames[arg3], state.GetVar(arg2), state.GetVar(arg1))));
			break;

		case OP_RETURN:
			if (arg0 == 0xff)
				state.PushStatement(StatementPtr(new ReturnStatement));
			else
				state.PushStatement(StatementPtr(new ReturnStatement(state.GetVar(arg1))));

			break;

		case OP_LOADNULLS:
			{
				ExpressionPtr nullExpr = ExpressionPtr(new NullExpression);

				for(int i = 0; i < arg1; ++i)
					state.SetVar(arg0 + i, nullExpr);
			}
			break;

		case OP_LOADROOTTABLE:
			state.SetVar(arg0, ExpressionPtr(new RootTableExpression));
			break;

		case OP_LOADBOOL:
			state.SetVar(arg0, ExpressionPtr(new LiteralConstantExpression( (arg1 != 0) ? "true" : "false" )));
			break;

		case OP_DMOVE:
			state.SetVar(arg0,  state.GetVar(arg1));
			state.SetVar(arg2,  state.GetVar(arg3));
			break;

		case OP_JMP:
			DecompileJumpInstruction(state, arg1);
			break;

		// *** OP_JNZ should not be matched - processed in do...while decompilation

		case OP_JZ:
			DecompileJumpZeroInstruction(state, arg0, arg1);
			break;

		case OP_LOADFREEVAR:
			state.SetVar(arg0, ExpressionPtr(new VariableExpression(m_OuterValues[arg1].name.GetString())));
			break;

		case OP_VARGC:
			state.SetVar(arg0, ExpressionPtr(new LiteralConstantExpression( "vargc" )));
			break;

		case OP_GETVARGV:
			state.SetVar(arg0, ExpressionPtr(new ArrayIndexingExpression(ExpressionPtr(new LiteralConstantExpression( "vargv" )),state.GetVar(arg1))));
			break;

		case OP_NEWTABLE:
			state.SetVar(arg0, ExpressionPtr(new NewTableExpression));
			break;

		case OP_NEWARRAY:
			state.SetVar(arg0, ExpressionPtr(new NewArrayExpression));
			break;

		case OP_APPENDARRAY:
			{
				ExpressionPtr arrayExp = state.GetVar(arg0);
				ExpressionPtr valueExp = (arg3 != 0) ? ExpressionPtr(new ConstantExpression(m_Literals[arg1])) : state.GetVar(arg1);

				if (arrayExp->GetType() == Exp_NewArrayExpression)
				{
					static_pointer_cast<NewArrayExpression>(arrayExp)->AddElement(valueExp);
					state.SetVar(arg0, arrayExp);
				}
				else
				{
					ExpressionPtr appendFunctionExp = ExpressionPtr(new ArrayIndexingExpression(arrayExp, ExpressionPtr(new ConstantExpression("append"))));
					shared_ptr<FunctionCallExpression> callExp = shared_ptr<FunctionCallExpression>(new FunctionCallExpression(appendFunctionExp));
					callExp->AddArgument(arrayExp);
					callExp->AddArgument(valueExp);

					state.PushStatement(StatementPtr(new ExpressionStatement(callExp)));
				}
			}
			break;

		case OP_GETPARENT:
			state.SetVar(arg0, ExpressionPtr(new ArrayIndexingExpression(state.GetVar(arg1), ExpressionPtr(new ConstantExpression("parent")))));
			break;
		
		case OP_COMPARITH:
			{
				ExpressionPtr leftArg = ExpressionPtr(new ArrayIndexingExpression(state.GetVar( ((unsigned int)arg1) >> 16 ), state.GetVar(arg2)));
				ExpressionPtr opExp = ExpressionPtr(new BinaryOperatorExpression((arg3 << 8) | '=', leftArg,  state.GetVar( 0x0000ffff & arg1 )));
				state.SetVar(arg0, opExp, true);
			}
			break;



		case OP_COMPARITHL:
			{
				ExpressionPtr opExp = ExpressionPtr(new BinaryOperatorExpression((arg3 << 8) | '=', state.GetVar(arg1), state.GetVar(arg2)));
				state.SetVar(arg0, opExp, true);
			}
			break;
			
		case OP_INC:
		case OP_INCL:
			{
				ExpressionPtr arg;
				if (code == OP_INC)
					arg = ExpressionPtr(new ArrayIndexingExpression(state.GetVar(arg1), state.GetVar(arg2)));
				else
					arg = state.GetVar(arg1);

				ExpressionPtr exp;
				if (op.arg3 > 0)
					exp = ExpressionPtr(new UnaryOperatorExpression('++', arg));
				else
					exp = ExpressionPtr(new UnaryOperatorExpression('--', arg));
				
				state.SetVar(arg0, exp, true);
			}
			break;

		case OP_PINC:
		case OP_PINCL:
			{
				ExpressionPtr arg;
				if (code == OP_PINC)
					arg = ExpressionPtr(new ArrayIndexingExpression(state.GetVar(arg1), state.GetVar(arg2)));
				else
					arg = state.GetVar(arg1);

				ExpressionPtr exp;
				if (op.arg3 > 0)
					exp = ExpressionPtr(new UnaryPostfixOperatorExpression('++', arg));
				else
					exp = ExpressionPtr(new UnaryPostfixOperatorExpression('--', arg));
				
				state.SetVar(arg0, exp, true);
			}
			break;

		case OP_CMP:
			state.SetVar(arg0, ExpressionPtr(new BinaryOperatorExpression(ComparisionOpcodeNames[arg3], state.GetVar(arg2), state.GetVar(arg1))));
			break;

		case OP_EXISTS:
			state.SetVar(arg0, ExpressionPtr(new BinaryOperatorExpression('in', state.GetVar(arg2), state.GetVar(arg1))));
			break;

		case OP_INSTANCEOF:
			state.SetVar(arg0, ExpressionPtr(new BinaryOperatorExpression(OperatorExpression::OPER_INSTANCEOF, state.GetVar(arg2), state.GetVar(arg1))));
			break;

		case OP_AND:
		case OP_OR:
			{
				ExpressionPtr leftArg = state.GetVar(arg2);

				int destIp = state.IP() + arg1;
				while(state.IP() < destIp && !state.EndOfInstructions())
				{
					if (state.IP() == (destIp - 1) && m_Instructions[state.IP()].op == OP_MOVE &&  static_cast<unsigned char>(m_Instructions[state.IP()].arg0) == arg0)
					{
						// Last move instruction of block - make simple move instead of variable set - that will be done later by logic operator
						state.NextInstruction();
						state.AtStack(arg0) = ToTemporaryVariable(state.GetVar(m_Instructions[state.IP() - 1].arg1));
					}
					else
					{
						DecompileStatement(state);
					}
				}

				ExpressionPtr opExpr = ExpressionPtr(new BinaryOperatorExpression((code == OP_OR) ? '||' : '&&', leftArg, state.GetVar(arg0)));
				state.SetVar(arg0, opExpr);
			}
			break;

		case OP_NEG:
			state.SetVar(arg0, ExpressionPtr(new UnaryOperatorExpression('-', state.GetVar(arg1))));
			break;

		case OP_NOT:
			state.SetVar(arg0, ExpressionPtr(new UnaryOperatorExpression('!', state.GetVar(arg1))));
			break;

		case OP_BWNOT:
			state.SetVar(arg0, ExpressionPtr(new UnaryOperatorExpression('~', state.GetVar(arg1))));
			break;

		case OP_CLOSURE:
			{
				shared_ptr<FunctionGeneratingExpression> func = shared_ptr<FunctionGeneratingExpression>(new FunctionGeneratingExpression(arg1, m_Functions[arg1]));

				for( vector<int>::const_iterator i = m_Functions[arg1].m_DefaultParams.begin(); i != m_Functions[arg1].m_DefaultParams.end(); ++i)
					func->AddDefault(state.GetVar(*i));

				state.SetVar(arg0, func);
			}
			break;

		case OP_YIELD:
			state.PushStatement(StatementPtr(new YieldStatement(
				(arg0 == 0xff) ? ExpressionPtr() : state.GetVar(arg1)
			)));
			break;

		case OP_RESUME:
			state.SetVar(arg0, ExpressionPtr(new UnaryOperatorExpression(OperatorExpression::OPER_RESUME, state.GetVar(arg1))));
			break;

		case OP_FOREACH:
			{
				// Initialize local variables that will be state of foreac loop
				state.InitVar(arg2,  ExpressionPtr(), true);
				state.InitVar(arg2 + 1,  ExpressionPtr(), true);
				state.InitVar(arg2 + 2,  ExpressionPtr(), true);

				ExpressionPtr objectExp = state.GetVar(arg0);
				ExpressionPtr keyExp = state.GetVar(arg2);
				ExpressionPtr valueExp = state.GetVar(arg2 + 1);
				ExpressionPtr refExp = state.GetVar(arg2 + 2);

				BlockStatementPtr block = state.PushBlock();

				// While block found - push loop block
				BlockState prevBlockState = state.m_BlockState;
				state.m_BlockState.inLoop = BlockState::ForeachLoop;
				state.m_BlockState.inSwitch = 0;
				state.m_BlockState.blockStart = state.IP() - 1;
				state.m_BlockState.blockEnd = state.IP() + arg1 - 1;
				state.m_BlockState.parent = &prevBlockState;

				int loopEndIp = state.IP() + arg1;

				// Remove variables initialization used only for 
				//while(!block->Statements().empty() && block->Statements().back()->GetType() == Stat_LocalVar)
				//{
				//	const shared_ptr<LocalVarInitStatement> var = static_pointer_cast<LocalVarInitStatement>(block->Statements().back());

				//	if (
				//		(refExp->GetType() == Exp_LocalVariable && var->GetStackAddress() == (arg2 + 2) && var->GetEndAddress() > state.IP() && var->GetEndAddress() < loopEndIp) ||
				//		(valueExp->GetType() == Exp_LocalVariable && var->GetStackAddress() == (arg2 + 1) && var->GetEndAddress() > state.IP() && var->GetEndAddress() < loopEndIp) ||
				//		(keyExp->GetType() == Exp_LocalVariable && var->GetStackAddress() == arg2 && var->GetEndAddress() >= state.IP() && var->GetEndAddress() < loopEndIp)
				//	   )
				//	{
				//		// Last block statement is a variable initialization that is a state of foreach loop - remove it
				//		block->Statements().pop_back();
				//	}
				//	else
				//	{
				//		break;
				//	}
				//}

				// Decompile loop block
				while(!state.EndOfInstructions() && state.IP() < loopEndIp)
				{
					if (state.IP() == (loopEndIp - 1) && m_Instructions[state.IP()].op == OP_JMP && m_Instructions[state.IP()].arg1 < 1)
					{
						// Skip loop ending JMP
						state.NextInstruction();
					}
					else
					{
						DecompileStatement(state);
					}
				}

				LoopBaseStatementPtr stat = LoopBaseStatementPtr(new ForeachStatement(keyExp, valueExp, objectExp, state.PopBlock(block)));
				stat->SetLoopBlock(state.m_BlockState);

				// Pop block state
				state.m_BlockState = prevBlockState;

				state.PushStatement(stat);
			}
			break;


		case OP_POSTFOREACH:
			// Ignore - used always after OP_FOREACH for generator iteration
			break;

		case OP_DELEGATE:
			state.SetVar(arg0, ExpressionPtr(new DelegateOperatorExpression(state.GetVar(arg2), state.GetVar(arg1))), true);
			break;
		
		case OP_CLONE:
			state.SetVar(arg0, ExpressionPtr(new UnaryOperatorExpression(OperatorExpression::OPER_CLONE, state.GetVar(arg1))));
			break;


		case OP_TYPEOF:
			state.SetVar(arg0, ExpressionPtr(new UnaryOperatorExpression(OperatorExpression::OPER_TYPEOF, state.GetVar(arg1))));
			break;

		case OP_PUSHTRAP:
			{
				// try catch statement
				BlockStatementPtr block = state.PushBlock();

				while(!state.EndOfInstructions())
				{
					if (m_Instructions[state.IP()].op == OP_POPTRAP)
					{
						state.NextInstruction();
						break;
					}

					DecompileStatement(state);
				}

				if (m_Instructions[state.IP()].op == OP_JMP)
				{
					BlockStatementPtr tryBlock = state.PushBlock();

					// second part - catch statement
					int jump_arg1 = m_Instructions[state.IP()].arg1;
					state.NextInstruction();

					// Search for local variable of exception handler
					state.AtStack(arg0) =  ExpressionPtr();
					std::string varName;

					for( vector<NutFunction::LocalVarInfo>::const_iterator i = m_Locals.begin(); i != m_Locals.end(); ++i )
						if (i->pos == arg0 && i->start_op == state.IP())
						{
							state.AtStack(arg0) = ExpressionPtr(new LocalVariableExpression(i->name));
							varName = i->name;
							break;
						};
		
					int destIp = state.IP() + jump_arg1;
					while(state.IP() < destIp && !state.EndOfInstructions())
					{
						DecompileStatement(state);
					}

					BlockStatementPtr catchBlock = state.PopBlock(block);

					state.PushStatement(StatementPtr(new TryCatchStatement(tryBlock, catchBlock, varName)));
				}
				else
				{
					state.PopBlock(block);
				}
			}
			break;


		// *** OP_POPTRAP case unspecified, used when parsing try...catch in OP_PUSHTRAP
		
		case OP_THROW:
			state.PushStatement(StatementPtr(new ThrowStatement(state.GetVar(arg0))));
			break;


		case OP_CLASS:
			{
				ExpressionPtr attributes;
				ExpressionPtr baseClass;

				if (arg1 != -1)
					baseClass = state.GetVar(arg1);

				if (arg2 != 0xff)
					attributes = state.GetVar(arg2);

				state.SetVar(arg0, ExpressionPtr(new NewClassExpression(baseClass, attributes)));
			}
			break;

		case OP_NEWSLOTA:
		case OP_NEWSLOT:
			{
				ExpressionPtr objExp = state.GetVar(arg1);
				ExpressionPtr keyExp = state.GetVar(arg2);
				ExpressionPtr valueExp = state.GetVar(arg3);

				if (objExp->GetType() == Exp_NewTableExpression)
				{
					static_pointer_cast<NewTableExpression>(objExp)->AddElement(keyExp, valueExp);
					state.SetVar(arg1, objExp);
				}
				else if (objExp->GetType() == Exp_NewClassExpression)
				{
					bool gotAttributes = (arg0 & 0x01) != 0;
					bool isStatic = (arg0 & 0x02) != 0;

					ExpressionPtr attributes;
					if (gotAttributes)
						attributes = state.GetVar(arg2 - 1);

					static_pointer_cast<NewClassExpression>(objExp)->AddElement(keyExp, valueExp, attributes, isStatic);
					state.SetVar(arg1, objExp);
				}
				else
				{
					shared_ptr<ArrayIndexingExpression> derefExp = shared_ptr<ArrayIndexingExpression>(new ArrayIndexingExpression(objExp, keyExp));
					if (valueExp->GetType() == Exp_Function && derefExp->IsSimpleMemberDeref())
					{
						
						if (objExp->GetType()==Exp_RootTable || objExp->GetType()==Exp_Operator)
						{
							//Exp_RootTable: for constructions like "::Variable <- function(...)"
							//Exp_Operator : for ArrayIndexingExpressions representing "::variable1.variable2 <- function (...)"
							ExpressionPtr slotExp = ExpressionPtr(new BinaryOperatorExpression('<-', derefExp, valueExp));
							state.PushStatement(StatementPtr(new ExpressionStatement(slotExp)));
						}
						else
						{
							shared_ptr<FunctionExpression> funcExp = static_pointer_cast<FunctionExpression>(valueExp);
							funcExp->SetName(derefExp->ToFunctionNameString());
							state.PushStatement(StatementPtr(new ExpressionStatement(funcExp)));
						}
					}
					else if (valueExp->GetType() == Exp_NewClassExpression && derefExp->IsSimpleMemberDeref())
					{
						shared_ptr<NewClassExpression> classExp = static_pointer_cast<NewClassExpression>(valueExp);
						classExp->SetName(derefExp->ToString());
						state.PushStatement(StatementPtr(new ExpressionStatement(classExp)));
					}
					else
					{
						ExpressionPtr slotExp = ExpressionPtr(new BinaryOperatorExpression('<-', derefExp, valueExp));
						state.PushStatement(StatementPtr(new ExpressionStatement(slotExp)));
					}
				}
			}
			break;

		default:
			state.PushUnknownOpcode();

			if (code != OP_JMP)
			{
				if (arg0 < m_StackSize)
					state.AtStack(arg0) =  ExpressionPtr();
			}

			break;
	}
}


// ***************************************************************************************************************
void NutFunction::DecompileJumpZeroInstruction( VMState& state, int arg0, int jumpOffset ) const
{
	if (jumpOffset > 0 && (state.IP() + jumpOffset) < (int)m_Instructions.size() && (state.IP() + jumpOffset) <= state.m_BlockState.blockEnd)
	{
		const Instruction& lastBlockOp = m_Instructions[state.IP() + jumpOffset - 1];
		if (lastBlockOp.op == OP_JMP && lastBlockOp.arg1 < -jumpOffset)
		{
			// Found conditional block with reverse jump at the end - potentially while loop
			// Check if last JMP is inside oure current block
			int blockLimit = state.m_BlockState.blockStart;
			if (state.m_BlockState.inLoop && state.m_BlockState.inLoop != BlockState::DoWhileLoop)
				blockLimit += 1;
				
			if ((state.IP() + jumpOffset + lastBlockOp.arg1) >= blockLimit)
			{
				// While block found - push loop block
				BlockState prevBlockState = state.m_BlockState;
				state.m_BlockState.inLoop = BlockState::WhileLoop;
				state.m_BlockState.inSwitch = 0;
				state.m_BlockState.blockStart = state.IP() + jumpOffset + lastBlockOp.arg1;
				state.m_BlockState.blockEnd = state.IP() + jumpOffset - 1;
				state.m_BlockState.parent = &prevBlockState;

				BlockStatementPtr block = state.PushBlock();
				ExpressionPtr condition = state.GetVar(arg0);

				int destIp = state.IP() + jumpOffset;
				while(state.IP() < destIp && !state.EndOfInstructions())
				{
					if (state.IP() == (destIp - 1) && m_Instructions[state.IP()].op == OP_JMP && m_Instructions[state.IP()].arg1 < 0)
					{
						// Skip loop jump
						state.NextInstruction();
					}
					else
					{
						DecompileStatement(state);
					}
				}

				LoopBaseStatementPtr stat = LoopBaseStatementPtr(new WhileStatement(condition, state.PopBlock(block)));
				stat->SetLoopBlock(state.m_BlockState);
				state.PushStatement(stat);

				// Pop block state
				state.m_BlockState = prevBlockState;

				return;
			}
		}
	}

	// Search for switch chain pattern
	if (jumpOffset > 0 && (state.IP() + jumpOffset) <= state.m_BlockState.blockEnd)
	{
		int pos1 = state.IP() + jumpOffset - 1;
		if (pos1 <= state.m_BlockState.blockEnd && m_Instructions[pos1].op == OP_JMP && m_Instructions[pos1].arg1 > 0)
		{
			int pos2 = pos1 + m_Instructions[pos1].arg1;  // +1 -1
			if (pos2 <= state.m_BlockState.blockEnd && m_Instructions[pos2].op == OP_JZ && m_Instructions[pos2].arg1 > 0)
			{
				// Found beggining of switch block with at least two case elements
				DecompileSwitchBlock(state);
				return;
			}
		}
	}


	if (jumpOffset >= 0 && (state.IP() + jumpOffset) <= state.m_BlockState.blockEnd)
	{
		// if instruction
		BlockStatementPtr block = state.PushBlock();
		BlockStatementPtr ifBlock, elseBlock;
		VMState::StackCopyPtr stackCopy;

		ExpressionPtr condition = state.GetVar(arg0);

		//bool elseMatch = false;
		int ifBlockEndIp = state.IP() + jumpOffset;
		int elseBlockEndIp = 0;
		bool gotElseBlock = false;
			
		if ((jumpOffset > 0) && (m_Instructions[ifBlockEndIp - 1].op == OP_JMP) && (m_Instructions[ifBlockEndIp - 1].arg1 >= 0))
		{
			// Last instruction of if block is unconditional forward jump - potentially else block
			elseBlockEndIp = ifBlockEndIp + m_Instructions[ifBlockEndIp - 1].arg1;

			// Check if this jump fits into current loop, otherwise it is break statement
			if (elseBlockEndIp <= state.m_BlockState.blockEnd)
			{
				gotElseBlock = true;
				stackCopy = state.CloneStack();
			}
		}
		
		BlockState prevBlockState = state.m_BlockState;
		state.m_BlockState.inLoop = 0;
		state.m_BlockState.inSwitch = 0;
		state.m_BlockState.blockStart = state.IP();
		state.m_BlockState.blockEnd = ifBlockEndIp;
		state.m_BlockState.parent = &prevBlockState;

		bool elseMatched = false;

		// Parse if block instructions
		while(state.IP() < ifBlockEndIp && !state.EndOfInstructions())
		{
			if (gotElseBlock && m_Instructions[state.IP()].op == OP_JMP && state.IP() == (ifBlockEndIp - 1))
			{
				// Skip else block jump
				state.NextInstruction();
				elseMatched = true;
			}
			else
			{
				DecompileStatement(state);
			}
		}

		if (!elseMatched)
			gotElseBlock = false;

		StatementPtr ifStatement;

		// Else block parsing
		if (gotElseBlock)
		{
			state.m_BlockState.blockStart = state.IP();
			state.m_BlockState.blockEnd = elseBlockEndIp;

			ifBlock = state.PushBlock();
			state.SwapStacks(stackCopy);

			while(state.IP() < elseBlockEndIp && !state.EndOfInstructions())
			{
				DecompileStatement(state);
			}

			elseBlock = state.PopBlock(block);
			state.m_BlockState = prevBlockState;
			
			ifStatement = StatementPtr(new IfStatement(condition, ifBlock, elseBlock));


			if (ifBlockEndIp > 2 && m_Instructions[ifBlockEndIp - 2].op != OP_JZ && m_Instructions[elseBlockEndIp - 1].op != OP_JMP)
			{
				int target1 = static_cast<unsigned char>(m_Instructions[ifBlockEndIp - 2].arg0);
				int target2 = static_cast<unsigned char>(m_Instructions[elseBlockEndIp - 1].arg0);

				if ((target1 == target2) && (target1 < m_StackSize) && state.AtStack(target1) && (state.AtStack(target1)->GetType() != Exp_LocalVariable) &&
					stackCopy->at(target1).expression && stackCopy->at(target1).expression->GetType() != Exp_LocalVariable)
				{
					// Block match condition operator - try to merge destination stack variables
					state.MergeStackVariable(condition, target1, stackCopy->at(target1), ifStatement);
				}
			}
		}
		else
		{
			state.m_BlockState = prevBlockState;

			ifBlock = state.PopBlock(block);
			ifStatement = StatementPtr(new IfStatement(condition, ifBlock, StatementPtr()));
		}			


		state.PushStatement(ifStatement);
		return;
	}


	// TODO: Unknown jump purpose
	state.PushUnknownOpcode();
}


// ***************************************************************************************************************
void NutFunction::DecompileDoWhileLoop( VMState& state, int jumpAddress ) const
{
	BlockState prevBlockState = state.m_BlockState;
	state.m_BlockState.inLoop = BlockState::DoWhileLoop;
	state.m_BlockState.inSwitch = 0;
	state.m_BlockState.blockStart = state.IP();
	state.m_BlockState.blockEnd = jumpAddress;
	state.m_BlockState.parent = &prevBlockState;

	BlockStatementPtr block = state.PushBlock();
	ExpressionPtr condition;

	int destIp = jumpAddress + 1;
	while(state.IP() < destIp && !state.EndOfInstructions())
	{
		if (state.IP() == jumpAddress && m_Instructions[state.IP()].op == OP_JNZ)
		{
			// Last jump instruction
			condition = state.GetVar( static_cast<unsigned char>(m_Instructions[state.IP()].arg0) );
			state.NextInstruction();
		}
		else
		{
			DecompileStatement(state);
		}
	}

	LoopBaseStatementPtr stat = LoopBaseStatementPtr(new DoWhileStatement(condition, state.PopBlock(block)));
	stat->SetLoopBlock(state.m_BlockState);
	state.PushStatement(stat);

	// Pop block state
	state.m_BlockState = prevBlockState;
}


// ***************************************************************************************************************
void NutFunction::DecompileJumpInstruction( VMState& state, int arg1 ) const
{
	// Most of jumps should be matched during blocks, loops and condition statements rebuild, unmatched jumps
	// may be signals of new loops or unstructural statements

	// Find closest loop block that we are in
	BlockState* outerNoLoopBlock = NULL;
	BlockState* loopBlock = &state.m_BlockState;

	while(loopBlock && !loopBlock->inLoop)
	{
		outerNoLoopBlock = loopBlock;
		loopBlock = loopBlock->parent;
	}

	if (loopBlock && (arg1 > 0) && ((state.IP() + arg1) == (loopBlock->blockEnd + 1)))
	{
		// Jump at the end of loop block - break statement
		state.PushStatement(StatementPtr(new BreakStatement));
		return;
	}


	if (loopBlock && (arg1 < 0) && ((state.IP() + arg1) == (loopBlock->blockStart)))
	{
		// Reverse jump at the beggining of loop block - continue statement;
		state.PushStatement(StatementPtr(new ContinueStatement));
		loopBlock->loopFlags |= BlockState::UsedBackwardJumpContinue;
		return;
	}


	if (loopBlock && loopBlock->inLoop == BlockState::DoWhileLoop && (arg1 > 0))
	{
		// Forward jump inside do...while loop that is not break - potentially condition statement
		if (!outerNoLoopBlock || (outerNoLoopBlock->blockEnd < (state.IP() + arg1)))
		{
			state.PushStatement(StatementPtr(new ContinueStatement));
			loopBlock->loopFlags |= BlockState::UsedForwardJumpContinue;
			return;
		}
	}

	// Jump still unmatched - try to match using lighter rules

	if (loopBlock && (arg1 < 0) && ((state.IP() + arg1) < state.m_BlockState.blockStart))
	{
		// Backward jump across current block - only continue statement can do that
		state.PushStatement(StatementPtr(new ContinueStatement));
		loopBlock->loopFlags |= BlockState::UsedBackwardJumpContinue;
		return;
	}

	// Check if we are in switch block
	BlockState* switchBlock = &state.m_BlockState;
	while(switchBlock && !switchBlock->inSwitch)
		switchBlock = switchBlock->parent;
	
	if (switchBlock && (arg1 >= 0) && ((state.IP() + arg1) >= switchBlock->blockEnd))
	{
		// Forward jump inside switch block - switch break statement
		switchBlock->blockEnd = state.IP() + arg1;
		state.PushStatement(StatementPtr(new BreakStatement));
		return;
	}

	if (loopBlock && loopBlock->inLoop == BlockState::WhileLoop && arg1 > 0)
	{
		// Forward jump inside while loop - probably continue statement of for loop
		state.PushStatement(StatementPtr(new ContinueStatement));
		loopBlock->loopFlags |= BlockState::UsedForwardJumpContinue;
		return;
	}

	// TODO: Other unmatched jump
	state.PushUnknownOpcode();
}

// ***************************************************************************************************************
void NutFunction::DecompileSwitchBlock( VMState& state ) const
{
	// Function is called after parsing OP_JZ instruction and detecting switch chain patter - previous instructin should be JZ
	assert(state.IP() > 0 && m_Instructions[state.IP() - 1].op == OP_JZ);

	// Initially scan trough switch chain to find switch block size (without default part)
	int pos = state.IP() - 1;
	for(;;)
	{
		if (pos <= state.m_BlockState.blockEnd && m_Instructions[pos].op == OP_JZ && m_Instructions[pos].arg1 > 0)
		{
			pos += m_Instructions[pos].arg1;
			
			if (pos <= state.m_BlockState.blockEnd && m_Instructions[pos].op == OP_JMP && m_Instructions[pos].arg1 > 0)
			{
				pos += m_Instructions[pos].arg1;
				continue;
			}
		}

		break;
	}

	// Move out of last instruction 
	pos += 1;

	// Check for common last break in switch block and eventually include it into
	// switch block
	if (pos < (int)m_Instructions.size() && m_Instructions[pos].op == OP_JMP && m_Instructions[pos].arg1 == 0)
		pos += 1;

	BlockState prevBlockState = state.m_BlockState;
	state.m_BlockState.inLoop = 0;
	state.m_BlockState.inSwitch = 1;
	state.m_BlockState.blockStart = state.IP() - 1;		// Not precise, but it is not important in case of switch
	state.m_BlockState.blockEnd = pos;					// Not includes default block, but will be corrected on break statement
	state.m_BlockState.parent = &prevBlockState;

	// Prepare switch block
	BlockStatementPtr block = state.PushBlock();

	ExpressionPtr switchVariable;		// Switch statement source variable expression

	ExpressionPtr condition = state.GetVar(m_Instructions[state.IP() - 1].arg0);
	int currentBlockEnd = state.IP() + m_Instructions[state.IP() - 1].arg1;

	for(;;)
	{
		ExpressionPtr caseValue;

		if (condition->GetType() == Exp_Operator)
		{
			shared_ptr<OperatorExpression> operatorExpression = static_pointer_cast<OperatorExpression>(condition);
			if (operatorExpression->GetOperatorType() == '==')
			{
				shared_ptr<BinaryOperatorExpression> comparisionOperator = static_pointer_cast<BinaryOperatorExpression>(condition);
				
				if (!switchVariable)
					switchVariable = comparisionOperator->GetArg1();

				caseValue = comparisionOperator->GetArg2();
			}
		}

		// Push start of current block
		state.PushStatement(StatementPtr(new CaseStatement(caseValue)));

		// Create fake blok for case part
		BlockState outCaseBlock = state.m_BlockState;
		state.m_BlockState.inLoop = 0;
		state.m_BlockState.inSwitch = 0;
		state.m_BlockState.blockStart = state.IP();
		state.m_BlockState.blockEnd = currentBlockEnd;
		state.m_BlockState.parent = &outCaseBlock;

		int nextBlockStart = -1;

		// Parse current block
		while(!state.EndOfInstructions() && state.IP() < currentBlockEnd)
		{
			if (state.IP() == (currentBlockEnd - 1) && m_Instructions[state.IP()].op == OP_JMP && m_Instructions[state.IP()].arg1 > 0 && (state.IP() + m_Instructions[state.IP()].arg1 + 1 < outCaseBlock.blockEnd))
			{
				// Last forward jump of block - element of switch chain
				if (m_Instructions[state.IP()].arg1 > 0)
					nextBlockStart = state.IP() + 1 + m_Instructions[state.IP()].arg1;

				state.NextInstruction();
			}
			else
			{
				DecompileStatement(state);
			}
		}

		state.m_BlockState = outCaseBlock;

		if (nextBlockStart > state.IP() && m_Instructions[nextBlockStart - 1].op == OP_JZ && m_Instructions[nextBlockStart - 1].arg1 >= 0)
		{
			// Parse expression till next case condition
			while(!state.EndOfInstructions() && state.IP() < (nextBlockStart - 1))
				DecompileStatement(state);
			
			if (state.IP() == (nextBlockStart - 1))
			{
				// Parse next case condition
				condition = state.GetVar(m_Instructions[state.IP()].arg0);
				currentBlockEnd = state.IP() + 1 + m_Instructions[state.IP()].arg1;
				state.NextInstruction();

				// Continue switch parsing
				continue;
			}
		}

		break;
	}

	if (state.IP() < state.m_BlockState.blockEnd)
	{
		// Parse default part
		state.PushStatement(StatementPtr(new CaseStatement(ExpressionPtr())));

		while(!state.EndOfInstructions() && state.IP() < state.m_BlockState.blockEnd)
			DecompileStatement(state);
	}

	state.m_BlockState = prevBlockState;
	BlockStatementPtr switchBlock = state.PopBlock(block);

	state.PushStatement(StatementPtr(new SwitchStatement(switchVariable, switchBlock)));	
}


// ***************************************************************************************************************
void NutFunction::PrintOpcode( std::ostream& out, int pos, const Instruction& op ) const
{
	unsigned int code = static_cast<unsigned int>(op.op);
	const char* codeName;

	if (code > OpcodesCount)
		codeName = "<invalid>";
	else
		codeName = OpcodeNames[code];

	out << "["; 
	out << std::setw(3) << std::setfill('0') << pos << std::setfill(' ');
	out << "]  " << codeName << spaces(14 - strlen(codeName));

	out << std::setw(5) << (int)op.arg0 << "  ";

	switch(code)
	{
		case OP_LOAD:
			out << m_Literals[op.arg1];
			break;

		case OP_DLOAD:
			out << m_Literals[op.arg1];
			out << std::setw(5) << (int)op.arg2;
			out << "  " << m_Literals[ static_cast<unsigned char>(op.arg3) ];
			break;

		case OP_LOADINT:
			out << std::setw(5) << op.arg1;
			break;

		case OP_LOADFLOAT:
			out << std::setw(5) << op.arg1_float;
			break;

		case OP_LOADBOOL:
			out << "  " << (op.arg1 ? "true" : "false");
			break;

		case OP_ARITH:
			out << '[' << (char)op.arg3 << "]  ";
			out << std::setw(5) << (int)op.arg1;
			out << std::setw(5) << (int)op.arg2;
			break;

		case OP_PREPCALLK:
		case OP_GETK:
			out << '(' << (int)op.arg2 << ")." << m_Literals[op.arg1].GetString() << "  ";
			out << std::setw(5) << (int)op.arg3;
			break;


	
			
		default:	
			
			//out << "  0x" << std::setw(8) << std::setfill('0') << std::setbase(16) << op.arg1 << std::setfill(' ') << std::setbase(10);
			out << std::setw(5) << (int)op.arg1;
			out << std::setw(5) << (int)op.arg2;
			out << std::setw(5) << (int)op.arg3;

			break;
	}
}

// ***************************************************************************************************************
void NutFunction::GenerateFunctionSource( int n, std::ostream& out, const std::string& name, const std::vector< std::string >& defaults ) const
{
	if (name != "constructor")
		out << "function ";
	out << name << '(';
	
	int paramsCount = 0;

	for(size_t i = 0; i < m_Parameters.size(); ++i)
	{
		if (i == 0 && m_Parameters[i] == "this")
			continue;

		if (paramsCount == 0)
			out << ' ';
		else
			out << ", ";

		out << m_Parameters[i];
		

		int defaultIndex = i - (m_Parameters.size() - defaults.size());
		if (defaultIndex >= 0)
		{
			out << " = " << defaults[defaultIndex];
		}

		paramsCount += 1;
	}

	if (m_GotVarParams)
	{
		if (paramsCount > 0)
			out << ", ";
		else
			out << ' ';

		out << "...";
		paramsCount += 1;
	}

	if (paramsCount > 0)
		out << ' ';

	out << ')';

	if (!m_OuterValues.empty())
	{
		out << " : ( " << m_OuterValues[0].name.GetString();
		for( size_t i = 1; i < m_OuterValues.size(); ++i)
			out << ", " << m_OuterValues[i].name.GetString();
		out << " )";
	}

	out << std::endl;

	out << indent(n) << "{" << std::endl;

	GenerateBodySource(n + 1, out);

	out << indent(n) << "}";// << std::endl;
	//out << std::endl;
	//out << std::endl;
}


// ***************************************************************************************************************
void NutFunction::GenerateBodySource( int n, std::ostream& out ) const
{
	//for( auto i = m_Functions.begin(); i != m_Functions.end(); ++i)
	//	i->GenerateFunctionSource(n, out, extraInfo);

	if (m_IsGenerator)
		out << indent(n) << "// Function is a generator." << std::endl;

	if (g_DebugMode)
	{
		out << indent(n) << "// Defaults:" << std::endl;
		for( std::vector<int>::const_iterator i = m_DefaultParams.begin(); i != m_DefaultParams.end(); ++i)
			out << indent(n) << "//\t" << *i << std::endl;
		
		out << std::endl;

		out << indent(n) << "// Literals:" << std::endl;
		for( std::vector<SqObject>::const_iterator i = m_Literals.begin(); i != m_Literals.end(); ++i)
			out << indent(n) << "//\t" << *i << std::endl;

		out << std::endl;

		out << indent(n) << "// Outer values:" << std::endl;
		for( vector<OuterValueInfo>::const_iterator i = m_OuterValues.begin(); i != m_OuterValues.end(); ++i)
			out << indent(n) << "//\t" << i->type << "  src=" << i->src << "  name=" << i->name << std::endl; 

		out << std::endl;

		out << indent(n) << "// Local identifiers:" << std::endl;
		for(vector<NutFunction::LocalVarInfo>::const_reverse_iterator i = m_Locals.rbegin(); i != m_Locals.rend(); ++i)
		{
			out << indent(n) << "//   -" << i->name << spaces(10 - i->name.size()) 
				<< " // pos=" << i->pos << "  start=" << i->start_op << "  end=" << i->end_op << (i->foreachLoopState ? " foreach state" : "") << std::endl;
		}

		out << std::endl;
		out << indent(n) << "// Instructions:" << std::endl;

		int64_t currentLine = 0;
		vector<LineInfo>::const_iterator lineInfo = m_LineInfos.begin();

		for(size_t i = 0; i < m_Instructions.size(); ++i)
		{
			while (lineInfo != m_LineInfos.end() && i >= (unsigned int)lineInfo->op)
			{
				currentLine = lineInfo->line;
				++lineInfo;
			}

			out << indent(n) << "// " << std::setfill(' ') << std::setw(5) << currentLine << "  ";
			PrintOpcode(out, (int)i, m_Instructions[i]);
			out << std::endl;
		}

		out << indent(n) << std::endl;
		out << indent(n) << "// Decompilation attempt:" << std::endl;
	}

	// Crate new state for decompiler virtual machine
	VMState state(*this, m_StackSize);

	// Set initial stack elements to local identifiers
	for(vector<NutFunction::LocalVarInfo>::const_reverse_iterator i = m_Locals.rbegin(); i != m_Locals.rend(); ++i)	
		if (i->start_op == 0 && !i->foreachLoopState)
			state.AtStack(i->pos) = ExpressionPtr(new LocalVariableExpression(i->name));

	// Decompiler loop
	while(!state.EndOfInstructions())
	{
		if (m_Instructions[state.IP()].op == OP_RETURN && (state.IP() == m_Instructions.size() - 1) && m_Instructions[state.IP()].arg0 == -1)
		{
			// This is last return statement in function - can be skipped
			state.NextInstruction();
			continue;	
		}

		DecompileStatement(state);
	}

	// Print decompiled code
	state.PrintOutput(out, n);
}
