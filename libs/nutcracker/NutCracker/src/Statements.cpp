
#include "Statements.h"
// ********************************************************************************************************
// *** Instructions block postprocessor *******************************************************************
// ********************************************************************************************************
StatementPtr BlockStatement::Postprocess( void )
{
	for( vector< StatementPtr >::iterator i = m_Statements.begin(); i != m_Statements.end(); )
	{
		*i = (*i)->Postprocess();

		if ((*i)->GetType() == Stat_While && i != m_Statements.begin())
		{
			shared_ptr<WhileStatement> whileStatement = static_pointer_cast<WhileStatement>(*i);
			StatementPtr forStatement = whileStatement->TryGenerateForStatement(i[-1]);

			if (forStatement)
			{
				i[-1] = forStatement;
				i = m_Statements.erase(i);
				continue;
			}
		}

		if ((*i)->IsEmpty())
		{
			i = m_Statements.erase(i);
			continue;
		}
		
		++i;;
	}

	if (m_Statements.empty())
		return EmptyStatement::Get();
	else if (m_Statements.size() == 1)
		return m_Statements[0];
	else
		return Statement::Postprocess();
}
