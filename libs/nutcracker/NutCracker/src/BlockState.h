
#pragma once

struct BlockState
{
	static const int WhileLoop = 1;
	static const int DoWhileLoop = 2;
	static const int ForeachLoop = 3;

	static const int UsedForwardJumpContinue = 0x01;
	static const int UsedBackwardJumpContinue = 0x02;

	unsigned char inLoop;
	unsigned char inSwitch;
	unsigned char loopFlags;

	int blockStart;		// First instruction of block (like beggining of condition expression)
	int blockEnd;		// First instruction after last functional instruction of block (without loop trail jump)

	BlockState* parent;

	BlockState()
	{
		inLoop = 0;
		inSwitch = 0;
		loopFlags = 0;
		
		blockStart = 0;
		blockEnd = 0x7fffffff;

		parent = NULL;
	}
};
