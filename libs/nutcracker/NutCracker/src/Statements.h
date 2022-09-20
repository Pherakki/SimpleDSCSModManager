
#pragma once

#include <memory>
#include <vector>
#include <ostream>

#include "Expressions.h"
#include "BlockState.h"
#include "Formatters.h"

// *******************************************************************************************
enum StatementType
{
	Stat_Empty,
	Stat_Expression,
	Stat_Block,
	Stat_LocalVar,
	Stat_Return,
	Stat_Throw,
	Stat_Yield,
	Stat_Break,
	Stat_Continue,
	Stat_Comment,
	Stat_Case,

	Stat_BEGIN_LINE_SEPARATED,

	Stat_If,
	Stat_TryCatch,
	Stat_For,
	Stat_While,
	Stat_DoWhile,
	Stat_Foreach,
	Stat_Switch,
};


// *******************************************************************************************
class Statement : public enable_shared_from_this<Statement>
{
public:
	virtual int GetType( void ) const = 0;
	virtual void GenerateCode( std::ostream& out, int indent ) const = 0;

	virtual shared_ptr<Statement> Postprocess( void )
	{
		return shared_from_this();
	}

	bool IsEmpty( void ) const			{ return GetType() == Stat_Empty;		}
	bool IsExpression( void ) const		{ return GetType() == Stat_Expression;	}
	bool IsBlock( void ) const			{ return GetType() == Stat_Block;		}

	void GenerateCodeInBlock( std::ostream& out, int indent ) const
	{
		if (IsBlock())
		{
			GenerateCode(out, indent);
		}
		else
		{
			out << ::indent(indent) << '{' << std::endl;
			GenerateCode(out, indent + 1);
			out << ::indent(indent) << '}' << std::endl;
		}
	}
};

typedef shared_ptr<Statement> StatementPtr;


// *******************************************************************************************
class EmptyStatement : public Statement
{
public:
	virtual int GetType( void ) const
	{
		return Stat_Empty;
	}

	virtual void GenerateCode( std::ostream&, int ) const
	{
	}

	static StatementPtr Get( void )
	{
		static StatementPtr s_instance;

		if (!s_instance)
			s_instance = StatementPtr(new EmptyStatement);

		return s_instance;
	}
};


// *******************************************************************************************
class ExpressionStatement : public Statement
{
private:
	ExpressionPtr m_Expression;

public:
	explicit ExpressionStatement( ExpressionPtr exp )
	{
		m_Expression = exp;
	}

	virtual int GetType( void ) const
	{
		return Stat_Expression;
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		if (!m_Expression)
			return;

		if (m_Expression->GetType() == Exp_NewClassExpression || m_Expression->GetType() == Exp_Function)
		{
			out << ::indent(n) << expression_out(m_Expression, n) << std::endl << std::endl;
		}
		else
		{
			out << ::indent(n) << expression_out(m_Expression, n) << ';' << std::endl;
		}
	}

	virtual StatementPtr Postprocess( void )
	{
		if (!m_Expression)
			return EmptyStatement::Get();

		return Statement::Postprocess();
	}

	void Clear( void )
	{
		m_Expression = shared_ptr<Expression>();
	}

	bool Equals( ExpressionPtr right ) const
	{
		return m_Expression == right;
	}

	const ExpressionPtr GetExpression( void ) const
	{
		return m_Expression;
	}
};

typedef shared_ptr<ExpressionStatement> ExpressionStatementPtr;


// *******************************************************************************************
class BlockStatement : public Statement
{
private:
	std::vector< StatementPtr > m_Statements;

public:
	BlockStatement()
	{
	}

	void Add( StatementPtr statement )
	{
		m_Statements.push_back(statement);
	}

	std::vector< StatementPtr >& Statements( void )
	{
		return m_Statements;
	}

	const std::vector< StatementPtr >& Statements( void ) const
	{
		return m_Statements;
	}	

	virtual int GetType( void ) const
	{
		return Stat_Block;
	}

	void GenerateBlockContentCode( std::ostream& out, int n ) const
	{
		StatementPtr prevStatement;
		bool pendingSpace = false;

		for( vector< StatementPtr >::const_iterator i = m_Statements.begin(); i != m_Statements.end(); ++i )
		{
			StatementPtr statement = *i;
			
			if (statement->GetType() == Stat_Case)
			{
				if (prevStatement)
					out << std::endl;

				statement->GenerateCode(out, std::max(0, n - 1));
				pendingSpace = false;
				prevStatement = StatementPtr();
				continue;
			}

			bool separatedStatement = statement->GetType() > Stat_BEGIN_LINE_SEPARATED;

			if (prevStatement && (separatedStatement || pendingSpace))
				out << std::endl;

			statement->GenerateCode(out, n);

			pendingSpace = separatedStatement;

			prevStatement = statement;
		}
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		out << ::indent(n) << '{' << std::endl;
		GenerateBlockContentCode(out, n + 1);
		out << ::indent(n) << '}' << std::endl;
	}

	virtual StatementPtr Postprocess( void );
};

typedef shared_ptr<BlockStatement> BlockStatementPtr;


// *******************************************************************************************
class IfStatement : public Statement
{
private:
	ExpressionPtr m_Condition;
	StatementPtr m_WhenTrue, m_WhenFalse;
	bool m_Canceled;

private:
	void _generateCode( std::ostream& out, int n ) const
	{
		out << "if (" << expression_out(m_Condition, n) << ')' << std::endl;
		m_WhenTrue->GenerateCodeInBlock(out, n);

		if (m_WhenFalse)
		{
			if (m_WhenFalse->GetType() == Stat_If)
			{
				out << ::indent(n) << "else ";
				static_pointer_cast<IfStatement>(m_WhenFalse)->_generateCode(out, n);
			}
			else
			{
				out << ::indent(n) << "else" << std::endl;
				m_WhenFalse->GenerateCodeInBlock(out, n);
			}
		}
	}

public:
	explicit IfStatement( ExpressionPtr condition, StatementPtr whenTrue, StatementPtr whenFalse )
	{
		m_Canceled = false;
		m_Condition = condition;
		m_WhenTrue = whenTrue;
		m_WhenFalse = whenFalse;
	}

	virtual int GetType( void ) const
	{
		return Stat_If;
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		out << ::indent(n);
		_generateCode(out, n);
	}

	const ExpressionPtr GetConditionExpression( void ) const
	{
		return m_Condition;
	}

	void Cancel( void )
	{
		m_Canceled = true;
	}

	virtual StatementPtr Postprocess( void )
	{
		m_WhenTrue = m_WhenTrue->Postprocess();

		if (m_WhenFalse)
			m_WhenFalse = m_WhenFalse->Postprocess();

		if (m_Canceled && m_WhenTrue->IsEmpty() && (!m_WhenFalse || m_WhenFalse->IsEmpty()))
			return EmptyStatement::Get();

		return Statement::Postprocess();
	}
};

// *******************************************************************************************
class LocalVarInitStatement : public Statement
{
private:
	std::string m_Name;
	ExpressionPtr m_Initialization;
	int64_t m_StackAddress;
	int64_t m_StartAddress;
	int64_t m_EndAddress;

public:
	explicit LocalVarInitStatement( const std::string& name, int64_t stackAddress, int64_t startAddress, int64_t endAddress, ExpressionPtr init = ExpressionPtr() )
	{
		m_Name = name;
		m_StackAddress = stackAddress;
		m_StartAddress = startAddress;
		m_EndAddress = endAddress;
		m_Initialization = init;
	}

	virtual int GetType( void ) const
	{
		return Stat_LocalVar;
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		out << ::indent(n) << "local " << m_Name;

		if (!m_Initialization)
			out << ';' << std::endl;
		else
			out << " = " << expression_out(m_Initialization, n) << ';' << std::endl;
	}

	const std::string& GetVarName( void ) const
	{
		return m_Name;
	}

	int64_t GetStackAddress( void ) const		{ return m_StackAddress;	}
	int64_t GetStartAddress( void ) const		{ return m_StartAddress;	}
	int64_t GetEndAddress( void ) const			{ return m_EndAddress;		}
};

// *******************************************************************************************
class ReturnStatement : public Statement
{
private:
	ExpressionPtr m_Expression;

public:
	ReturnStatement()
	{
	}

	explicit ReturnStatement( ExpressionPtr retExpr )
	{
		m_Expression = retExpr;
	}

	virtual int GetType( void ) const
	{
		return Stat_Return;
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		if (!m_Expression)
			out << ::indent(n) << "return;" << std::endl;
		else
			out << ::indent(n) << "return " << expression_out(m_Expression, n) << ';' << std::endl;
	}
};

// *******************************************************************************************
class ThrowStatement : public Statement
{
private:
	ExpressionPtr m_Expression;

public:
	explicit ThrowStatement( ExpressionPtr retExpr )
	{
		m_Expression = retExpr;
	}

	virtual int GetType( void ) const
	{
		return Stat_Throw;
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		out << ::indent(n) << "throw " << expression_out(m_Expression, n) << ';' << std::endl;
	}
};

// *******************************************************************************************
class YieldStatement : public Statement
{
private:
	ExpressionPtr m_Expression;

public:
	explicit YieldStatement( ExpressionPtr retExpr )
	{
		m_Expression = retExpr;
	}

	virtual int GetType( void ) const
	{
		return Stat_Yield;
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		if (m_Expression)
			out << ::indent(n) << "yield " << expression_out(m_Expression, n) << ';' << std::endl;
		else
			out << ::indent(n) << "yield;" << std::endl;
	}
};

// *******************************************************************************************
class TryCatchStatement : public Statement
{
private:
	StatementPtr m_Try, m_Catch;
	std::string m_CatchVariable;



public:
	explicit TryCatchStatement( StatementPtr tryStatement, StatementPtr catchStatement, const std::string& varName )
	{
		m_Try = tryStatement;
		m_Catch = catchStatement;
		m_CatchVariable = varName;
	}

	virtual int GetType( void ) const
	{
		return Stat_TryCatch;
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		out << ::indent(n) << "try" << std::endl;
		m_Try->GenerateCodeInBlock(out, n);
		out << ::indent(n) << "catch( " << m_CatchVariable << " )" << std::endl;
		m_Catch->GenerateCodeInBlock(out, n);
	}

	virtual StatementPtr Postprocess( void )
	{
		m_Try = m_Try->Postprocess();
		m_Catch = m_Catch->Postprocess();

		return Statement::Postprocess();
	}
};


// *******************************************************************************************
class BreakStatement : public Statement
{
public:
	virtual int GetType( void ) const
	{
		return Stat_Break;
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		out << ::indent(n) << "break;" << std::endl;
	}
};

// *******************************************************************************************
class ContinueStatement : public Statement
{
public:
	virtual int GetType( void ) const
	{
		return Stat_Continue;
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		out << ::indent(n) << "continue;" << std::endl;
	}
};

// *******************************************************************************************
class CommentStatement : public Statement
{
private:
	std::string m_Text;

public:
	explicit CommentStatement( const std::string& text )
	{
		m_Text = text;
	}

	virtual int GetType( void ) const
	{
		return Stat_Comment;
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		out << ::indent(n) << "  // " << m_Text << std::endl;
	}
};


// *******************************************************************************************
class LoopBaseStatement : public Statement
{
protected:
	int m_LoopStartAddress;
	int m_LoopEndAddress;
	int m_LoopFlags;

public:
	void SetLoopBlock( const BlockState& blockState )
	{
		m_LoopStartAddress = blockState.blockStart;
		m_LoopEndAddress = blockState.blockEnd;
		m_LoopFlags = blockState.loopFlags;

		if (blockState.inLoop)
			m_LoopEndAddress += 1;	// Last JMP of loop
	}

	void SetLoopBlock( const LoopBaseStatement& other )
	{
		m_LoopStartAddress = other.m_LoopStartAddress;
		m_LoopEndAddress = other.m_LoopEndAddress;
		m_LoopFlags = other.m_LoopFlags;
	}

	int GetLoopStartAddress( void ) const		{ return m_LoopStartAddress;	}
	int GetLoopEndAddress( void ) const			{ return m_LoopEndAddress;		}
};

typedef shared_ptr<LoopBaseStatement> LoopBaseStatementPtr;


// *******************************************************************************************
class ForStatement : public LoopBaseStatement
{
private:
	StatementPtr m_Initialization, m_Incrementation;
	ExpressionPtr m_Condition;
	StatementPtr m_Block;

public:
	explicit ForStatement( StatementPtr initialization, ExpressionPtr condition, StatementPtr incrementation, StatementPtr block )
	{
		m_Initialization = initialization;
		m_Condition = condition;
		m_Incrementation = incrementation;
		m_Block = block;
	}

	virtual int GetType( void ) const
	{
		return Stat_For;
	}

	void GenerateStatementInline( std::ostream& out, int n, StatementPtr statement ) const
	{
		std::ostringstream statementBuffer;
		statement->GenerateCode(statementBuffer, 0);

		std::string text = statementBuffer.str();

		while (!text.empty() && (text[text.length()-1] == '\n' || text[text.length()-1] == ';'))
			text.resize(text.length()-1); //remove last element

		AssureIndents(text, n);

		out << text;
	}


	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		out << ::indent(n) << "for( ";
		
		if (m_Initialization)
			GenerateStatementInline(out, n, m_Initialization);

		out << "; ";

		if (m_Condition)
			m_Condition->GenerateCode(out, n);

		out << "; ";

		if (m_Incrementation)
			GenerateStatementInline(out, n, m_Incrementation);
		
		out << " )" << std::endl;
		m_Block->GenerateCodeInBlock(out, n);
	}

	virtual StatementPtr Postprocess( void )
	{
		m_Block = m_Block->Postprocess();
		return Statement::Postprocess();
	}
};

// *******************************************************************************************
class WhileStatement : public LoopBaseStatement
{
private:
	ExpressionPtr m_Condition;
	StatementPtr m_Block;


public:
	explicit WhileStatement( ExpressionPtr condition, StatementPtr block )
	{
		m_Condition = condition;
		m_Block = block;
	}

	virtual int GetType( void ) const
	{
		return Stat_While;
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		out << ::indent(n) << "while (" << expression_out(m_Condition, n) << ')' << std::endl;
		m_Block->GenerateCodeInBlock(out, n);
	}

	virtual StatementPtr Postprocess( void )
	{
		m_Block = m_Block->Postprocess();

		return Statement::Postprocess();
	}

	StatementPtr GetForIncrementStatement( void )
	{
		if (m_Block->GetType() != Stat_Block)
			return StatementPtr();

		shared_ptr<BlockStatement> block = static_pointer_cast<BlockStatement>(m_Block);
		if (block->Statements().size() < 1 || block->Statements().back()->GetType() != Stat_Expression)
			return StatementPtr();

		const ExpressionPtr lastExpresion = static_pointer_cast<ExpressionStatement>(block->Statements().back())->GetExpression();
		if (!lastExpresion || !lastExpresion->IsOperator())
			return  StatementPtr();

		int opType = static_pointer_cast<OperatorExpression>(lastExpresion)->GetOperatorType();
		if (opType != '++' && opType != '--' && opType != '+=' && opType != '-=' && opType != '=')
			return StatementPtr();

		StatementPtr ret = block->Statements().back();
		block->Statements().pop_back();

		return ret;
	}

	StatementPtr TryGenerateForStatement( StatementPtr prevStatement )
	{
		if (m_LoopFlags & BlockState::UsedBackwardJumpContinue)
			return  StatementPtr();

		if (prevStatement->GetType() == Stat_LocalVar)
		{
			shared_ptr<LocalVarInitStatement> localVar = static_pointer_cast<LocalVarInitStatement>(prevStatement);
			if (localVar->GetEndAddress() < m_LoopStartAddress || localVar->GetEndAddress() >= m_LoopEndAddress)
				return  StatementPtr();
		}
		else if (prevStatement->GetType() != Stat_Expression)
		{
			return  StatementPtr();
		}

		StatementPtr incrementStatement = GetForIncrementStatement();

		if ((prevStatement->GetType() != Stat_LocalVar) && !incrementStatement)
			return  StatementPtr();

		LoopBaseStatementPtr forStatement = LoopBaseStatementPtr(new ForStatement(prevStatement, m_Condition, incrementStatement, m_Block));
		forStatement->SetLoopBlock(*this);

		return forStatement;
	}
};


// *******************************************************************************************
class DoWhileStatement : public LoopBaseStatement
{
private:
	ExpressionPtr m_Condition;
	StatementPtr m_Block;

public:
	explicit DoWhileStatement( ExpressionPtr condition, StatementPtr block )
	{
		m_Condition = condition;
		m_Block = block;
	}

	virtual int GetType( void ) const
	{
		return Stat_DoWhile;
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		out << ::indent(n) << "do" << std::endl;
		m_Block->GenerateCodeInBlock(out, n);
		out << ::indent(n) << "while (" << expression_out(m_Condition, n) << ");" << std::endl;
	}

	virtual StatementPtr Postprocess( void )
	{
		m_Block = m_Block->Postprocess();

		return Statement::Postprocess();
	}
};


// *******************************************************************************************
class ForeachStatement : public LoopBaseStatement
{
private:
	ExpressionPtr m_Key, m_Value, m_Object;
	StatementPtr m_Block;

public:
	explicit ForeachStatement( ExpressionPtr key, ExpressionPtr value, ExpressionPtr object, StatementPtr block )
	{
		m_Key = key;
		m_Value = value;
		m_Object = object;
		m_Block = block;
	}

	virtual int GetType( void ) const
	{
		return Stat_Foreach;
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		out << ::indent(n) << "foreach( ";
		
		if (m_Key && (!m_Key->IsVariable() || static_pointer_cast<VariableExpression>(m_Key)->GetVariableName() != "@INDEX@"))
			out << expression_out(m_Key, n) << ", ";

		out << expression_out(m_Value, n) << " in " << expression_out(m_Object, n) << " )" << std::endl;

		m_Block->GenerateCodeInBlock(out, n);
	}

	virtual StatementPtr Postprocess( void )
	{
		m_Block = m_Block->Postprocess();

		return Statement::Postprocess();
	}
};

// *******************************************************************************************
class SwitchStatement : public Statement
{
private:
	ExpressionPtr m_Variable;
	StatementPtr m_Block;

public:
	explicit SwitchStatement( ExpressionPtr variable, StatementPtr block )
	{
		m_Variable = variable;
		m_Block = block;
	}

	virtual int GetType( void ) const
	{
		return Stat_Switch;
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		out << ::indent(n) << "switch(" << expression_out(m_Variable, n) << ')' << std::endl;
		m_Block->GenerateCodeInBlock(out, n);
	}

	virtual StatementPtr Postprocess( void )
	{
		m_Block = m_Block->Postprocess();

		return Statement::Postprocess();
	}
};

// *******************************************************************************************
class CaseStatement : public Statement
{
private:
	ExpressionPtr m_Value;

public:
	explicit CaseStatement( ExpressionPtr value )
	{
		m_Value = value;
	}

	virtual int GetType( void ) const
	{
		return Stat_Case;
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		if (m_Value)
			out << ::indent(n) << "case " << expression_out(m_Value, n) << ':' << std::endl;
		else
			out << ::indent(n) << "default:" << std::endl;
	}
};

