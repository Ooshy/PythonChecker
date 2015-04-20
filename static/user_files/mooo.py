#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  untitled.py
#  
#  Copyright 2013 Chris Zimmerman <chris@chris-X202E>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
class Animal():
	def __init__(self, position):
		self.cow = "Moo"
		self.position = position
		
		moo = []
		for i in range(10):
			for j in range(10):
				moo.append((i,j))
		self.grid = moo
		
	def moo(self):
		print(self.cow)
	def move(self, direction):
		if direction == 'up':
			if (self.position[0],self.position[1]+1) in self.grid:
				self.position = (self.position[0],self.position[1]+1)
			else:
				pass
		elif direction == 'left':
			if (self.position[0]-1,self.position[1]) in self.grid:
				self.position = (self.position[0]-1,self.position[1])
			else:
				pass
		elif direction == 'right':
			if (self.position[0]+1,self.position[1]) in self.grid:
				self.position = (self.position[0]+1,self.position[1])
			else:
				pass
		elif direction == 'down':
			if (self.position[0],self.position[1]-1) in self.grid:
				self.position = (self.position[0],self.position[1]-1)
			else:
				pass
	def getPosition(self):
		return self.position

def main():
	mike = Animal((4,3))
	print(mike.getPosition())
	mike.move('up')
	print(mike.getPosition())

	
	return 0

if __name__ == '__main__':
	main()

