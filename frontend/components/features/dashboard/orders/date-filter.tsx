"use client"

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { format } from "date-fns";
import { CalendarIcon, Filter } from "lucide-react";
import { es } from "date-fns/locale";

interface DateFilterProps {
  onDateChange: (startDate: string | null, endDate: string | null) => void;
}

export function DateFilter({ onDateChange }: DateFilterProps) {
  const [startDate, setStartDate] = useState<Date | undefined>(undefined);
  const [endDate, setEndDate] = useState<Date | undefined>(undefined);
  const [isOpen, setIsOpen] = useState<boolean>(false);

  const handleApplyFilter = () => {
    onDateChange(
      startDate ? format(startDate, 'yyyy-MM-dd') : null,
      endDate ? format(endDate, 'yyyy-MM-dd') : null
    );
    setIsOpen(false);
  };

  const handleQuickFilter = (days: number) => {
    if (days === 0) {
      // Hoy
      const today = new Date();
      setStartDate(today);
      setEndDate(today);
      
      // Aplicar filtro inmediatamente
      onDateChange(
        format(today, 'yyyy-MM-dd'),
        format(today, 'yyyy-MM-dd')
      );
    } else if (days === -1) {
      // Ayer
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      setStartDate(yesterday);
      setEndDate(yesterday);
      
      // Aplicar filtro inmediatamente
      onDateChange(
        format(yesterday, 'yyyy-MM-dd'),
        format(yesterday, 'yyyy-MM-dd')
      );
    } else if (days > 0) {
      // Últimos X días
      const end = new Date();
      const start = new Date();
      start.setDate(start.getDate() - days);
      setStartDate(start);
      setEndDate(end);
      
      // Aplicar filtro inmediatamente
      onDateChange(
        format(start, 'yyyy-MM-dd'),
        format(end, 'yyyy-MM-dd')
      );
    } else {
      // Todas (30 días por defecto)
      setStartDate(undefined);
      setEndDate(undefined);
      onDateChange(null, null);
    }
    
    // Cerrar el popover después de aplicar un filtro rápido
    setIsOpen(false);
  };

  const handleResetFilter = () => {
    setStartDate(undefined);
    setEndDate(undefined);
    onDateChange(null, null);
    setIsOpen(false);
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className="h-8 gap-1">
          <Filter className="h-3.5 w-3.5" />
          <span>Filtrar por fecha</span>
          {(startDate || endDate) && (
            <span className="ml-1 rounded-full bg-primary w-2 h-2" />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-4" align="start">
        <div className="space-y-4">
          <div className="grid gap-2">
            <h4 className="font-medium text-sm">Filtros rápidos</h4>
            <div className="flex flex-wrap gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => handleQuickFilter(0)}
              >
                Hoy
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => handleQuickFilter(-1)}
              >
                Ayer
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => handleQuickFilter(7)}
              >
                Últimos 7 días
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => handleQuickFilter(30)}
              >
                Últimos 30 días
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleResetFilter}
              >
                Todas
              </Button>
            </div>
          </div>
          
          <div className="grid gap-2">
            <h4 className="font-medium text-sm">Rango personalizado</h4>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Desde</p>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full justify-start text-left font-normal"
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {startDate ? (
                        format(startDate, 'PP', { locale: es })
                      ) : (
                        <span>Seleccionar</span>
                      )}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={startDate}
                      onSelect={setStartDate}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Hasta</p>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full justify-start text-left font-normal"
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {endDate ? (
                        format(endDate, 'PP', { locale: es })
                      ) : (
                        <span>Seleccionar</span>
                      )}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={endDate}
                      onSelect={setEndDate}
                      initialFocus
                      disabled={(date) => 
                        startDate ? date < startDate : false
                      }
                    />
                  </PopoverContent>
                </Popover>
              </div>
            </div>
          </div>
          
          <div className="flex justify-end space-x-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setIsOpen(false)}
            >
              Cancelar
            </Button>
            <Button 
              size="sm" 
              onClick={handleApplyFilter}
            >
              Aplicar
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
} 