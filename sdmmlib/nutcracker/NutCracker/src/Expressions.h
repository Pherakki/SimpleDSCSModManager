
#pragma once

#include <iostream>
#include <sstream>
#include <memory>
#include <string>

#include "SqObject.h"
#include "Formatters.h"

using namespace std;

// ************************************************************************************************************************************
enum ExpressionType
{
	Exp_Constant,
	Exp_RootTable,
	Exp_Null,
	Exp_Variable,
	Exp_LocalVariable,
	Exp_Operator,
	Exp_MemberAccess,
	Exp_Function,
	Exp_FunctionCall,
	Exp_NewTableExpression,
	Exp_NewArrayExpression,
	Exp_NewClassExpression,
};


// ************************************************************************************************************************************
class Expression
{
public:
	virtual int GetType( void ) const = 0;
	//virtual std::string ToString( void ) const = 0;
	virtual void GenerateCode( std::ostream& out, int indent ) const = 0;

	bool IsOperator( void ) const		{ return GetType() == Exp_Operator;										}
	bool IsVariable( void ) const		{ return GetType() == Exp_Variable || GetType() == Exp_LocalVariable;	}
};

typedef shared_ptr<Expression> ExpressionPtr;

struct expression_out
{
	ExpressionPtr m_expr;
	int m_indent;

	explicit expression_out( ExpressionPtr expr, int n ) : m_expr(expr), m_indent(n) {}

	friend std::ostream& operator << ( std::ostream& out, const expression_out& e )
	{
		e.m_expr->GenerateCode(out, e.m_indent);
		return out;
	}
};


// ************************************************************************************************************************************
// ************************************************************************************************************************************
class VariableExpression : public Expression
{
private:
	std::string m_name;

public:
	explicit VariableExpression( const std::string& name )
	: m_name(name)
	{
	}

	virtual int GetType( void ) const
	{
		return Exp_Variable;
	}

	virtual void GenerateCode( std::ostream& out, int ) const
	{
		out << m_name;
	}

	const std::string& GetVariableName( void ) const
	{
		return m_name;
	}
};


// *****************************************************************************************
class LocalVariableExpression : public VariableExpression
{
public:
	explicit LocalVariableExpression( const std::string& name )
	: VariableExpression(name)
	{
	}

	virtual int GetType( void ) const
	{
		return Exp_LocalVariable;
	}
};


// *****************************************************************************************
class ConstantExpression : public Expression
{
protected:
	std::string m_text;
	bool m_isLiteral;

	char ToHex( int value )
	{
		if (value < 10)
			return '0' + value;
		else if (value < 16)
			return 'a' + (value - 10);
		else
			return '0';
	}

	ConstantExpression()
	{
		m_isLiteral = false;
	}


public:
	explicit ConstantExpression( const std::string& str )
	{
		set(str);
	}

	explicit ConstantExpression( unsigned int value )
	{
		set(value);
	}

	explicit ConstantExpression( float value )
	{
		set(value);
	}

	explicit ConstantExpression( const SqObject& obj )
	{
		switch(obj.GetType())
		{
			default:
			case SqObject::TypeNull:
				m_isLiteral = true;
				m_text.clear();
				break;

			case SqObject::TypeString:
				set(obj.GetString());
				break;

			case SqObject::TypeInteger:
				set(obj.GetInteger());
				break;

			case SqObject::TypeFloat:
				set(obj.GetFloat());
				break;
		}
	}


	void set( const std::string& str )
	{
		m_text.clear();
		m_text.reserve(str.size() + 2);

		m_text += '\"';
		for( basic_string <char>::const_iterator i = str.begin(); i != str.end(); ++i)
		{
			switch(*i)
			{
				case '\"':	m_text += "\\\"";			break;
				case '\'':	m_text += "\\\'";			break;
				case '\r':	m_text += "\\r";			break;
				case '\n':	m_text += "\\n";			break;
				case '\t':	m_text += "\\t";			break;
				case '\v':	m_text += "\\v";			break;
				case '\a':	m_text += "\\a";			break;
				case '\\':	m_text += "\\\\";			break;
			
				default:
					{
						const char c = *i;

						if (c < 0x20 || c > 0x7e)
						{
							m_text += "\\x00";
							m_text += ToHex((c >> 4) & 0x0f);
							m_text += ToHex(c & 0x0f);
						}
						else
						{
							m_text += c;
						}
					}
					break;
			}
		}
		m_text += '\"';

		m_isLiteral = true;
	}


	void set( unsigned int value )
	{
		std::ostringstream builder(std::ios_base::out);

		builder << value;

		m_isLiteral = false;
		m_text = builder.str();
	}


	void set( float value )
	{
		std::ostringstream builder(std::ios_base::out);

		builder.precision(8);
		builder << value;

		if (builder.str().find('.') == std::string::npos)
			builder << ".0";

		m_isLiteral = false;
		m_text = builder.str();
	}


	virtual int GetType( void ) const
	{
		return Exp_Constant;
	}


	virtual void GenerateCode( std::ostream& out, int ) const
	{
		out << m_text;
	}


	bool IsLiteral( void ) const
	{
		return m_isLiteral;
	}


	bool IsLabel( void ) const
	{
		if (!m_isLiteral || m_text.size() < 3)
			return false;

		for(int i = 1; i < (int)(m_text.size() - 1); ++i)
		{
			char c = m_text[i];

			bool isValidChar = 
				(i > 1 && c >= '0' && c <= '9') ||
				(c >= 'a' && c <= 'z') ||
				(c >= 'A' && c <= 'Z') ||
				c == '_';

			if (!isValidChar)
				return false;
		}

		return true;
	}


	std::string GetLabel( void ) const
	{
		if (!m_isLiteral || m_text.size() < 3)
			return m_text;

		return m_text.substr(1, m_text.size() - 2);
	}

	static shared_ptr<ConstantExpression> AsLabelExpression( ExpressionPtr exp )
	{
		if (exp->GetType() != Exp_Constant)
			return shared_ptr<ConstantExpression>();

		shared_ptr<ConstantExpression> constExpr = static_pointer_cast<ConstantExpression>(exp);
		
		if (constExpr->IsLabel())
			return constExpr;
		else
			return shared_ptr<ConstantExpression>();
	}
};


// *****************************************************************************************
class LiteralConstantExpression : public ConstantExpression
{
public:
	explicit LiteralConstantExpression( const char* name )
	{
		m_text = name;
	}
};


// *****************************************************************************************
class RootTableExpression : public Expression
{
public:
	RootTableExpression()
	{
	}


	virtual int GetType( void ) const
	{
		return Exp_RootTable;
	}


	virtual void GenerateCode( std::ostream& out, int ) const
	{
		out << "getroottable()";
	}
};


// *****************************************************************************************
class NullExpression : public Expression
{
public:
	NullExpression()
	{
	}


	virtual int GetType( void ) const
	{
		return Exp_Null;
	}


	virtual void GenerateCode( std::ostream& out, int ) const
	{
		out << "null";
	}
};


// *****************************************************************************************
class OperatorExpression : public Expression
{
public:
	static const int OPER_MASK = 0xffff0000;
	static const int OPER_SPECIAL_MARKER = 0xff000000;

	static const int OPER_INSTANCEOF =	OPER_SPECIAL_MARKER | 1;
	static const int OPER_TYPEOF =		OPER_SPECIAL_MARKER | 2;
	static const int OPER_CLONE =		OPER_SPECIAL_MARKER | 3;
	static const int OPER_DELETE =		OPER_SPECIAL_MARKER | 4;
	static const int OPER_RESUME =		OPER_SPECIAL_MARKER | 5;
	static const int OPER_DELEGATE =	OPER_SPECIAL_MARKER | 6;
	static const int OPER_ARRAYIND =	OPER_SPECIAL_MARKER | 7;

protected:
	int m_operator;

	OperatorExpression()
	{
	}


protected:
	void GenerateOpName( std::ostream& out ) const
	{
		int op = m_operator;
		if (!op) return;

		if ((op & OPER_MASK) == OPER_SPECIAL_MARKER)
		{
			// Special operator name
			switch(op)
			{
				case OPER_INSTANCEOF:
					out << "instanceof";
					break;

				case OPER_TYPEOF:
					out << "typeof";
					break;

				case OPER_CLONE:
					out << "clone";
					break;

				case OPER_DELETE:
					out << "delete";
					break;

				case OPER_RESUME:
					out << "resume";
					break;
			}
		}
		else
		{
			// 1..4 characters operator coded in int

			while(0 == (0xff000000 & op)) op <<= 8;
		
			while(op != 0)
			{
				out << (char)(op >> 24);
				op <<= 8;
			}
		}
	}


	void GenerateArgument( std::ostream& out, int n, ExpressionPtr arg, bool parenthesis ) const
	{
		if (parenthesis)
		{
			out << '(';
			arg->GenerateCode(out, n);
			out << ')';
		}
		else
		{
			arg->GenerateCode(out, n);
		}
	}


public:
	virtual int GetType( void ) const
	{
		return Exp_Operator;
	}

	int GetOperatorType( void ) const
	{
		return m_operator;
	}

	virtual int GetOperatorPriority( void ) const = 0;
};


// *****************************************************************************************
class UnaryOperatorExpression : public OperatorExpression
{
protected:
	ExpressionPtr m_arg;


public:
	explicit UnaryOperatorExpression( int op, ExpressionPtr arg )
	{
		m_operator = op;
		m_arg = arg;
	}


	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		GenerateOpName(out);

		if (OPER_SPECIAL_MARKER == (m_operator & OPER_MASK))
			out << ' ';

		bool parenthesis = m_arg->IsOperator() && (static_pointer_cast<OperatorExpression>(m_arg)->GetOperatorPriority() < this->GetOperatorPriority());
		GenerateArgument(out, n, m_arg, parenthesis);
	}


	virtual int GetOperatorPriority( void ) const
	{
		return 200;
	}
};


// *****************************************************************************************
class UnaryPostfixOperatorExpression : public OperatorExpression
{
protected:
	ExpressionPtr m_arg;

public:
	explicit UnaryPostfixOperatorExpression( int op, ExpressionPtr arg )
	{
		m_operator = op;
		m_arg = arg;
	}


	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		std::string text;
		
		bool parenthesis = m_arg->IsOperator() && (static_pointer_cast<OperatorExpression>(m_arg)->GetOperatorPriority() < this->GetOperatorPriority());
		GenerateArgument(out, n, m_arg, parenthesis);

		if (OPER_SPECIAL_MARKER == (m_operator & OPER_MASK))
			out << ' ';

		GenerateOpName(out);
	}


	virtual int GetOperatorPriority( void ) const
	{
		return 300;
	}
};


// *****************************************************************************************
class BinaryOperatorExpression : public OperatorExpression
{
protected:
	ExpressionPtr m_arg1, m_arg2;

public:
	explicit BinaryOperatorExpression( int op, ExpressionPtr arg1, ExpressionPtr arg2 )
	{
		m_operator = op;
		m_arg1 = arg1;
		m_arg2 = arg2;
	}

	
	ExpressionPtr GetArg1( void )		{ return m_arg1;	}
	ExpressionPtr GetArg2( void )		{ return m_arg2;	}


	virtual void GenerateCode( std::ostream& out, int n ) const
	{	
		int myPriority = GetOperatorPriority();
		bool rightToLeft = 0 != (myPriority & 1);

		bool leftParenthesis = false;
		bool rightParenthesis = false;

		if (m_arg1->IsOperator())
		{
			if (!rightToLeft)
			{
				if (static_pointer_cast<OperatorExpression>(m_arg1)->GetOperatorPriority() < myPriority)
					leftParenthesis = true;
			}
			else
			{
				if (static_pointer_cast<OperatorExpression>(m_arg1)->GetOperatorPriority() <= myPriority)
					leftParenthesis = true;
			}
		}

		if (m_arg2->IsOperator())
		{
			if (!rightToLeft)
			{
				if (static_pointer_cast<OperatorExpression>(m_arg2)->GetOperatorPriority() <= myPriority)
					rightParenthesis = true;
			}
			else
			{
				if (static_pointer_cast<OperatorExpression>(m_arg2)->GetOperatorPriority() < myPriority)
					rightParenthesis = true;
			}
		}

		GenerateArgument(out, n, m_arg1, leftParenthesis);
		out << ' ';
		GenerateOpName(out);
		out << ' ';
		GenerateArgument(out, n, m_arg2, rightParenthesis);
	}


	virtual int GetOperatorPriority( void ) const
	{
		switch(m_operator)
		{
			case '/':
			case '*':
			case '%':
				return 100;

			case '+':
			case '-':
				return 98;

			case '<<':
			case '>>':
			case '>>>':
				return 96;

			case '<':
			case '<=':
			case '>':
			case '>=':
				return 94;

			case '==':
			case '!=':
				return 92;

			case '&':	return 90;
			case '^':	return 88;
			case '|':	return 86;

			case '&&':
			case 'in':
				return 85;

			case '||':
				return 83;

			// 70 - ?:

			// 60 - delegate

			case '=':
			case '<-':
			case '+=':
			case '-=':
			case '/=':
			case '*=':
			case '%=':
			case '|=':
			case '&=':
			case '^=':
				return 51;

			default:
				return -100;
		}
	}
};

// *****************************************************************************************
class ConditionOperatorExpression : public OperatorExpression
{
private:
	ExpressionPtr m_condition;
	ExpressionPtr m_whenTrue, m_whenFalse;

public:
	explicit ConditionOperatorExpression( ExpressionPtr condition, ExpressionPtr whenTrue, ExpressionPtr whenFalse )
	{
		m_operator = '?:';
		m_condition = condition;
		m_whenTrue = whenTrue;
		m_whenFalse = whenFalse;
	}


	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		int myPriority = GetOperatorPriority();
		bool condParethesis = (m_condition->IsOperator() && (static_pointer_cast<OperatorExpression>(m_condition)->GetOperatorPriority() <= myPriority));
		bool arg1Parenthesis = (m_whenTrue->IsOperator() && (static_pointer_cast<OperatorExpression>(m_whenTrue)->GetOperatorPriority() <= myPriority));
		bool arg2Parenthesis = (m_whenFalse->IsOperator() && (static_pointer_cast<OperatorExpression>(m_whenFalse)->GetOperatorPriority() < myPriority));

		GenerateArgument(out, n, m_condition, condParethesis);
		out << " ? ";
		GenerateArgument(out, n, m_whenTrue, arg1Parenthesis);
		out << " : ";
		GenerateArgument(out, n, m_whenFalse, arg2Parenthesis);
	}


	virtual int GetOperatorPriority( void ) const
	{
		return 60;
	}

	ExpressionPtr GetConditionExp( void ) const		{ return m_condition;	}
	ExpressionPtr GetTrueExp( void ) const			{ return m_whenTrue;	}
	ExpressionPtr GetFalseExp( void ) const			{ return m_whenFalse;	}
};

// *****************************************************************************************
class DelegateOperatorExpression : public OperatorExpression
{
protected:
	ExpressionPtr m_arg1, m_arg2;

public:
	explicit DelegateOperatorExpression( ExpressionPtr arg1, ExpressionPtr arg2 )
	{
		m_operator = OPER_DELEGATE;
		m_arg1 = arg1;
		m_arg2 = arg2;
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		out << "delegate ";
		
		int myPriority = GetOperatorPriority();
		bool arg1Parenthesis = (m_arg1->IsOperator() && (static_pointer_cast<OperatorExpression>(m_arg1)->GetOperatorPriority() <= myPriority));
		bool arg2Parenthesis = (m_arg2->IsOperator() && (static_pointer_cast<OperatorExpression>(m_arg2)->GetOperatorPriority() <= myPriority));

		GenerateArgument(out, n, m_arg1, arg1Parenthesis);
		out << " : ";
		GenerateArgument(out, n, m_arg2, arg2Parenthesis);
	}

	virtual int GetOperatorPriority( void ) const
	{
		return 60;
	}
};


// *****************************************************************************************
class ArrayIndexingExpression : public OperatorExpression
{
protected:
	ExpressionPtr m_obj;
	ExpressionPtr m_indexer;


public:
	explicit ArrayIndexingExpression( ExpressionPtr obj, ExpressionPtr indexer )
	{
		m_operator = OPER_ARRAYIND;
		m_obj = obj;
		m_indexer = indexer;
	}

	bool IsSimpleMemberDeref( void ) const
	{
		if (!ConstantExpression::AsLabelExpression(m_indexer))
			return false;

		if (m_obj->GetType() == Exp_Operator && static_pointer_cast<OperatorExpression>(m_obj)->GetOperatorType() == OPER_ARRAYIND)
		{
			return static_pointer_cast<ArrayIndexingExpression>(m_obj)->IsSimpleMemberDeref();
		}
		else if (m_obj->GetType() == Exp_RootTable)
		{
			return true;
		}
		else if (m_obj->IsVariable())
		{
			return static_pointer_cast<VariableExpression>(m_obj)->GetVariableName() == "this";	// TODO: Check for local variable deref
			//return true;
		}
		else
		{
			return false;
		}
	}

	void GenerateCode( std::ostream& out, int n, const char* labelsDelimiter, bool allowExplicitThis ) const
	{
		bool parenthesis = 
			m_obj->IsOperator() &&
			static_pointer_cast<OperatorExpression>(m_obj)->GetOperatorPriority() < this->GetOperatorPriority();

		shared_ptr<ConstantExpression> labelIndexer = ConstantExpression::AsLabelExpression(m_indexer);
		if (labelIndexer)
		{
			// Indexer is a valid string label - we can change array indexing to member access (a["b"] -> a.b)
			if (m_obj->GetType() == Exp_RootTable)
			{
				out <<  "::";
			}
			else if (m_obj->GetType() == Exp_Operator && static_pointer_cast<OperatorExpression>(m_obj)->GetOperatorType() == OPER_ARRAYIND)
			{
				static_pointer_cast<ArrayIndexingExpression>(m_obj)->GenerateCode(out, n, labelsDelimiter, allowExplicitThis);
				out << labelsDelimiter;
			}
			else if (m_obj->IsVariable())
			{
				// TODO: Removal of this when there is no local variable of this same name
				if (static_pointer_cast<VariableExpression>(m_obj)->GetVariableName() != "this" || allowExplicitThis)
				{
					m_obj->GenerateCode(out, n);
					out << labelsDelimiter;
				}
			}
			else
			{
				GenerateArgument(out, n, m_obj, parenthesis);
				out << labelsDelimiter;
			}

			out << labelIndexer->GetLabel();
			return;
		}

		GenerateArgument(out, n, m_obj, parenthesis);
		out << '[';
		m_indexer->GenerateCode(out, n);
		out << ']';
	}

	std::string ToString( void ) const
	{
		std::ostringstream buffer;
		GenerateCode(buffer, 0);
		return buffer.str();
	}

	std::string ToFunctionNameString( void ) const
	{
		std::ostringstream buffer;
		GenerateCode(buffer, 0, "::", false);
		return buffer.str();
	}

	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		GenerateCode(out, n, ".", true);
	}


	virtual int GetOperatorPriority( void ) const
	{
		return 300;
	}
};


// *****************************************************************************************
class FunctionCallExpression : public Expression
{
private:
	ExpressionPtr m_function;
	std::vector<ExpressionPtr> m_arguments;


public:
	explicit FunctionCallExpression( ExpressionPtr func )
	{
		m_function = func;
	}

	void AddArgument( ExpressionPtr arg )
	{
		m_arguments.push_back(arg);
	}


	virtual int GetType( void ) const
	{
		return Exp_FunctionCall;
	}


	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		m_function->GenerateCode(out, n);
		out << '(';
		
		for( size_t i = 0; i < m_arguments.size(); ++i)
		{
			if (i > 0)
				out << ", ";

			m_arguments[i]->GenerateCode(out, n);
		}

		out << ')';
	}
};


// ***************************************************************************************************************
class FunctionExpression : public Expression
{
protected:
	std::string m_name;
	int m_FunctionIndex;

public:
	explicit FunctionExpression( int functionIndex )
	: m_FunctionIndex(functionIndex)
	{
	}

	void SetName( const std::string& name )
	{
		m_name = name;
	}

	virtual int GetType( void ) const
	{
		return Exp_Function;
	}
};


// *****************************************************************************************
class TableBaseExpression : public Expression
{
protected:
	void GenerateElementCode( ExpressionPtr key, ExpressionPtr value, char eolChar, std::ostream& out, int n ) const;
};


// *****************************************************************************************
class NewTableExpression : public TableBaseExpression
{
private:
	std::vector< std::pair<ExpressionPtr, ExpressionPtr> > m_Elements;


public:
	NewTableExpression()
	{
	}


	virtual int GetType( void ) const
	{
		return Exp_NewTableExpression;
	}


	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		if (m_Elements.empty())
		{
			out << "{}";
			return;
		}

		out << "{" << std::endl;
		for( vector< std::pair<ExpressionPtr, ExpressionPtr> >::const_iterator i = m_Elements.begin(); i != m_Elements.end(); ++i)
		{
			out << ::indent(n + 1);
			GenerateElementCode(i->first, i->second, (*i != m_Elements.back()) ? ',' : 0, out, n + 1);
			out << std::endl;
		}

		out << ::indent(n) << '}';
	}


	virtual void GenerateAttributesCode( std::ostream& out, int n ) const
	{
		out << "</ ";
		for( vector< std::pair<ExpressionPtr, ExpressionPtr> >::const_iterator i = m_Elements.begin(); i != m_Elements.end(); ++i)
		{
			GenerateElementCode(i->first, i->second, (*i != m_Elements.back()) ? ',' : 0, out, n);
		}
		out << " />";
	}


	void AddElement( ExpressionPtr key, ExpressionPtr value )
	{
		m_Elements.push_back( std::pair<ExpressionPtr, ExpressionPtr>(key, value) );
	}
};

// *****************************************************************************************
class NewArrayExpression : public Expression
{
private:
	std::vector< ExpressionPtr > m_Elements;


public:
	NewArrayExpression()
	{
	}


	virtual int GetType( void ) const
	{
		return Exp_NewArrayExpression;
	}


	virtual void GenerateCode( std::ostream& out, int n ) const
	{
		if (m_Elements.empty())
		{
			out << "[]";
			return;
		}

		out << "[" << std::endl;
		for( vector< ExpressionPtr >::const_iterator i = m_Elements.begin(); i != m_Elements.end(); ++i)
		{
			out << ::indent(n + 1);
			(*i)->GenerateCode(out, n + 1);
			
			if (*i != m_Elements.back())
				out << ',';
			
			out << std::endl;
		}

		out << ::indent(n) << ']';
	}


	void AddElement( ExpressionPtr value )
	{
		m_Elements.push_back(value);
	}
};

// *****************************************************************************************
class NewClassExpression : public TableBaseExpression
{
private:
	struct ClassElement
	{
		ExpressionPtr key;
		ExpressionPtr value;
		ExpressionPtr attributes;

		bool isStatic;
	};

	std::string m_Name;
	ExpressionPtr m_BaseClass;
	ExpressionPtr m_Attributes;

	std::vector< ClassElement > m_Elements;

public:
	explicit NewClassExpression( ExpressionPtr BaseClass, ExpressionPtr Attributes )
	{
		m_BaseClass = BaseClass;
		m_Attributes = Attributes;
	}

	void SetName( const std::string& name )
	{
		m_Name = name;
	}

	virtual int GetType( void ) const
	{
		return Exp_NewClassExpression;
	}

	void GenerateCode( std::ostream& out, int n ) const
	{
		out << "class ";

		if (!m_Name.empty())
			out << m_Name  << ' ';
		
		if (m_BaseClass)
		{
			out << "extends ";
			m_BaseClass->GenerateCode(out, n);
		}

		if (m_Attributes && m_Attributes->GetType() == Exp_NewTableExpression)
		{
			out << ' ';
			static_pointer_cast<NewTableExpression>(m_Attributes)->GenerateAttributesCode(out, n);
		}

		out << std::endl;
		out << ::indent(n) << '{' << std::endl;
		for( vector< ClassElement >::const_iterator i = m_Elements.begin(); i != m_Elements.end(); ++i)
		{
			if (i->attributes && i->attributes->GetType() == Exp_NewTableExpression)
			{
				out << ::indent(n + 1);
				static_pointer_cast<NewTableExpression>(i->attributes)->GenerateAttributesCode(out, n);
				out << std::endl;
			}

			out << ::indent(n +	1);

			if (i->isStatic)
				out << "static ";

			GenerateElementCode(i->key, i->value, ';', out, n + 1);
			out << std::endl;			
		}

		out << ::indent(n) << '}';
	}

	void AddElement( ExpressionPtr key, ExpressionPtr value, ExpressionPtr attributes, bool isStatic )
	{
		ClassElement element;
		element.key = key;
		element.value = value;
		element.attributes = attributes;
		element.isStatic = isStatic;

		m_Elements.push_back(element);
	}
};


// ******************************************************************************************************************************************************************************
inline void TableBaseExpression::GenerateElementCode( ExpressionPtr key, ExpressionPtr value, char eolChar, std::ostream& out, int n ) const
{
	if (value->GetType() == Exp_Function || value->GetType() == Exp_NewClassExpression)
	{
		// Member function or nested class - find its name
		std::string name;
			
		shared_ptr<ConstantExpression> labelExp = ConstantExpression::AsLabelExpression(key);
		if (labelExp)
		{
			name = labelExp->GetLabel();
		}
		else if (key->GetType() == Exp_Operator && static_pointer_cast<OperatorExpression>(key)->GetOperatorType() == OperatorExpression::OPER_ARRAYIND)
		{
			shared_ptr<ArrayIndexingExpression> derefExp = static_pointer_cast<ArrayIndexingExpression>(key);
			if (derefExp->IsSimpleMemberDeref())
			{
				if (value->GetType() == Exp_Function)
					name = derefExp->ToFunctionNameString();
				else
					name = derefExp->ToString();
			}
		}

		if (!name.empty())
		{
			if (value->GetType() == Exp_Function)
			{
				shared_ptr<FunctionExpression> func = static_pointer_cast<FunctionExpression>(value);
				func->SetName(name);
			}
			else
			{
				shared_ptr<NewClassExpression> newClass = static_pointer_cast<NewClassExpression>(value);
				newClass->SetName(name);
			}

			value->GenerateCode(out, n);
			out << std::endl;
			return;
		}
	}

	shared_ptr<ConstantExpression> labelExp = ConstantExpression::AsLabelExpression(key);
	if (labelExp)
	{
		out << labelExp->GetLabel();
	}
	else
	{
		out << '[';
		key->GenerateCode(out, n);
		out << ']';
	}

	out << " = ";
	value->GenerateCode(out, n);

	if (eolChar != 0)
		out << eolChar;
}
